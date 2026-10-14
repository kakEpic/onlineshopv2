from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.views.generic import View, TemplateView
from django.utils.translation import gettext_lazy as _

from apps.customer.models import Customer
from apps.order.models import Order, OrderDetail, Notification
from apps.payment.service import generate_order_qr
from .cart import Cart
from .checkout_forms import GuestCheckoutForm, RegisteredUserCheckoutForm
from .services import send_order_notification, send_websocket_notification


class CheckoutView(View):
    """
    Checkout view - handles both guest and registered users.
    """
    template_name = 'cart/checkout.html'

    def get(self, request):
        cart = Cart(request)

        # Check if cart is empty
        if cart.is_empty():
            messages.warning(request, _('Your cart is empty.'))
            return redirect('products:client_list')

        context = {
            'cart': cart,
            'cart_items': cart.get_items(),
        }

        # Different forms for guest vs registered users
        if request.user.is_authenticated:
            # Pre-fill with user info
            initial_data = {}
            if hasattr(request.user, 'customer_profile'):
                customer = request.user.customer_profile
                initial_data['shipping_address'] = customer.address
            context['form'] = RegisteredUserCheckoutForm(initial=initial_data)
            context['is_guest'] = False
        else:
            context['form'] = GuestCheckoutForm()
            context['is_guest'] = True

        return render(request, self.template_name, context)

    def post(self, request):
        cart = Cart(request)

        if cart.is_empty():
            messages.warning(request, _('Your cart is empty.'))
            return redirect('products:client_list')

        if request.user.is_authenticated:
            return self._process_registered_checkout(request, cart)
        else:
            return self._process_guest_checkout(request, cart)

    def _process_guest_checkout(self, request, cart):
        """Process checkout for guest users."""
        form = GuestCheckoutForm(request.POST)

        if form.is_valid():
            # Create customer
            customer = form.save(commit=False)
            customer.save()

            # Create order
            order = self._create_order(
                cart=cart,
                customer=customer,
                user=None,
                shipping_address=customer.address,
                note=customer.note
            )

            # Generate payment QR and clear cart
            generate_order_qr(order)
            cart.clear()

            # Send real-time admin notification only
            send_websocket_notification(order)

            messages.success(
                request,
                _('Your order has been created. Scan the QR code to pay.')
            )
            return redirect('payment:order_payment', pk=order.pk)

        context = {
            'cart': cart,
            'cart_items': cart.get_items(),
            'form': form,
            'is_guest': True,
        }
        return render(request, self.template_name, context)

    def _process_registered_checkout(self, request, cart):
        """Process checkout for registered users."""
        form = RegisteredUserCheckoutForm(request.POST)

        if form.is_valid():
            # Get or create customer profile
            customer, created = Customer.objects.get_or_create(
                user=request.user,
                defaults={
                    'name': request.user.get_full_name() or request.user.email,
                    'phone': getattr(request.user, 'phone', '') or '',
                    'address': form.cleaned_data['shipping_address']
                }
            )

            # Update address if needed
            if not created:
                customer.address = form.cleaned_data['shipping_address']
                customer.save()

            # Create order
            order = self._create_order(
                cart=cart,
                customer=customer,
                user=request.user,
                shipping_address=form.cleaned_data['shipping_address'],
                note=form.cleaned_data.get('note', '')
            )

            # Generate payment QR and clear cart
            generate_order_qr(order)
            #cart.clear()

            # Send notifications
            send_order_notification(order, request.user)
            send_websocket_notification(order)  # Real-time admin notification

            messages.success(
                request,
                _('Your order has been created. Scan the QR code to pay.')
            )
            return redirect('payment:order_payment', pk=order.pk)

        context = {
            'cart': cart,
            'cart_items': cart.get_items(),
            'form': form,
            'is_guest': False,
        }
        return render(request, self.template_name, context)

    def _create_order(self, cart, customer, user, shipping_address, note):
        """Create order from cart."""
        order = Order.objects.create(
            customer=customer,
            user=user,
            status=Order.Status.PENDING,
            shipping_address=shipping_address,
            note=note
        )

        # Create order details
        total = Decimal('0')
        for item in cart.get_items():
            line_total = item['price'] * item['quantity']
            OrderDetail.objects.create(
                order=order,
                product=item['product'],
                product_name=item['product'].name,
                price=item['price'],
                qty=item['quantity']
            )
            total += line_total

            # Update product total_sold
            from django.db.models import F
            item['product'].__class__.objects.filter(pk=item['product'].pk).update(
                total_sold=F('total_sold') + item['quantity']
            )
        # Update order total
        order.total = total
        order.save(update_fields=['total'])

        return order


class OrderSuccessView(TemplateView):
    """Display order success page."""
    template_name = 'cart/order_success.html'

    def get(self, request, *args, **kwargs):
        cart = Cart(request)
        cart.clear()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = get_object_or_404(Order, pk=kwargs['pk'])
        context['order'] = order
        return context
