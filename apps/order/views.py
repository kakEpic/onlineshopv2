from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    View
)

from apps.cart.services import send_order_status_notification, send_telegram_status_update
from .models import Order, Notification
from .forms import (
    OrderForm,
    OrderDetailFormSet
)


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to restrict access to admin users only."""
    def test_func(self):
        return self.request.user.is_staff


# ============== Client Views ==============

class MyOrdersView(LoginRequiredMixin, ListView):
    """List of orders for logged-in user."""
    model = Order
    template_name = 'orders/client/my_orders.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).select_related('customer')


class OrderDetailClientView(LoginRequiredMixin, DetailView):
    """Order detail view for clients."""
    model = Order
    template_name = 'orders/client/order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class NotificationListView(LoginRequiredMixin, ListView):
    """List notifications for logged-in user."""
    model = Notification
    template_name = 'orders/client/notifications.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class MarkNotificationReadView(LoginRequiredMixin, View):
    """Mark a notification as read."""

    def post(self, request, pk):
        notification = get_object_or_404(
            Notification,
            pk=pk,
            user=request.user
        )
        notification.mark_as_read()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})

        return redirect('orders:notifications')


class MarkAllNotificationsReadView(LoginRequiredMixin, View):
    """Mark all notifications as read."""

    def post(self, request):
        Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})

        return redirect('orders:notifications')


# ============== Admin/Dashboard Views ==============

class OrderListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """Admin order list."""
    model = Order
    template_name = 'orders/dashboard/list.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        queryset = Order.objects.select_related('customer', 'user')

        # Filter by status
        status = self.request.GET.get('status')
        if status and status in dict(Order.Status.choices):
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Order.Status.choices
        context['current_status'] = self.request.GET.get('status', '')
        return context


class OrderDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    """Admin order detail."""
    model = Order
    template_name = 'orders/dashboard/detail.html'
    context_object_name = 'order'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Order.Status.choices
        return context


class OrderStatusUpdateView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Update order status."""

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        new_status = request.POST.get('status')

        if new_status in dict(Order.Status.choices):
            old_status = order.status
            order.status = new_status
            order.save(update_fields=['status', 'updated_at'])

            # Send notifications
            if order.user:
                send_order_status_notification(order)
            send_telegram_status_update(order)

            messages.success(
                request,
                _('Order status updated to %(status)s') %
                {'status': order.get_status_display()}
            )
        else:
            messages.error(request, _('Invalid status'))

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'status': order.status,
                'status_display': order.get_status_display()
            })

        return redirect('orders:dashboard_detail', pk=pk)


class OrderCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """Admin order create view."""
    model = Order
    form_class = OrderForm
    template_name = 'orders/dashboard/form.html'
    success_url = reverse_lazy('orders:dashboard_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context['formset'] = OrderDetailFormSet(self.request.POST)
        else:
            context['formset'] = OrderDetailFormSet()

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        if formset.is_valid():

            self.object = form.save()

            formset.instance = self.object

            formset.save()

            return redirect(
                self.success_url
            )

        return self.form_invalid(form)