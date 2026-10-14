import base64
import os
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.order.models import Order
from apps.cart.services import send_order_status_notification, send_telegram_status_update
from .service import check_order_payment, generate_order_qr
from django.views.generic import TemplateView, View

try:
    from bakong_khqr import KHQR
except ImportError:  # pragma: no cover
    KHQR = None


def get_khqr_client():
    if KHQR is None:
        raise ImproperlyConfigured(
            'The bakong_khqr package is required to generate Bakong QR payments.'
        )
    return KHQR(settings.BAKONG_API_TOKEN)


def create_qr_payload(order: Order) -> str:
    client = get_khqr_client()
    return client.create_qr(
        account_id=settings.BAKONG_MERCHANT_ID,
        merchant_name=settings.BAKONG_MERCHANT_NAME,
        merchant_city=settings.BAKONG_MERCHANT_CITY,
        amount=float(order.total),
        currency=settings.BAKONG_CURRENCY,
        bill_number=str(order.invoice_no),
        store_label=settings.BAKONG_MERCHANT_NAME,
        static=False,
    )


def create_qr_image_data(qr_payload: str) -> str:
    client = get_khqr_client()
    image_result = client.qr_image(qr_payload)

    if isinstance(image_result, bytes):
        return 'data:image/png;base64,' + base64.b64encode(image_result).decode()

    if isinstance(image_result, str):
        if os.path.exists(image_result):
            with open(image_result, 'rb') as f:
                encoded = base64.b64encode(f.read()).decode()
            return 'data:image/png;base64,' + encoded
        return image_result

    return ''


def attach_qr_to_order(order: Order, qr_payload: str, qr_image: str, md5: str) -> Order:
    order.khqr = qr_payload
    order.qr_image = qr_image
    order.md5 = md5
    order.save(update_fields=['khqr', 'qr_image', 'md5'])
    return order


def generate_order_qr(order: Order) -> Order:
    qr_payload = create_qr_payload(order)
    client = get_khqr_client()
    md5 = client.generate_md5(qr_payload)
    qr_image = create_qr_image_data(qr_payload)
    return attach_qr_to_order(order, qr_payload, qr_image, md5)


def check_order_payment(order: Order) -> str:
    client = get_khqr_client()
    status = client.check_payment(order.md5)
    if status and status.upper() == 'PAID' and order.status != Order.Status.PAID:
        order.status = Order.Status.PAID
        order.save(update_fields=['status'])
        if order.user:
            send_order_status_notification(order)
        send_telegram_status_update(order)
    return status


def checkout_view(request):
    if request.method != 'POST':
        return redirect('cart:checkout')

    total = request.POST.get('total', '0')
    try:
        total_value = Decimal(total)
    except Exception:
        total_value = Decimal('0.00')

    order = Order.objects.create(
        customer=request.user.customer_profile if request.user.is_authenticated else None,
        user=request.user if request.user.is_authenticated else None,
        total=total_value,
        status=Order.Status.PENDING,
    )
    generate_order_qr(order)
    return redirect('payment:order_payment', pk=order.pk)


class OrderPaymentView(TemplateView):
    template_name = 'payment/order_payment.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = get_object_or_404(Order, pk=kwargs['pk'])
        context['order'] = order
        return context


class CheckPaymentStatusView(View):

    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        status = check_order_payment(order)

        return JsonResponse({
            'status': status,
            'order_status': order.status,
        })


class OrderPaymentSuccessView(TemplateView):
    template_name = 'payment/success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order'] = get_object_or_404(Order, pk=kwargs['pk'])
        return context