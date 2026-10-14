from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import TemplateView

from apps.products.models import Product
from apps.order.models import Order
from .cart import Cart
from .forms import CartAddProductForm, CartUpdateForm


class CartDetailView(TemplateView):
    """Display the cart."""
    template_name = 'cart/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = Cart(self.request)
        context['cart'] = cart
        context['cart_items'] = cart.get_items()
        context['update_form'] = CartUpdateForm()
        return context


class CartAddView(View):
    """Add a product to the cart."""

    def post(self, request, product_id):
        cart = Cart(request)
        product = get_object_or_404(
            Product,
            id=product_id,
            is_visible_to_client=True
        )

        form = CartAddProductForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            cart.add(
                product=product,
                quantity=cd['quantity'],
                override_quantity=cd['override']
            )

        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'cart_count': len(cart),
                'cart_total': str(cart.get_total_price()),
                'message': f'{product.name} added to cart'
            })

        return redirect('cart:detail')


class CartRemoveView(View):
    """Remove a product from the cart."""

    def post(self, request, product_id):
        cart = Cart(request)
        product = get_object_or_404(Product, id=product_id)
        cart.remove(product)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'cart_count': len(cart),
                'cart_total': str(cart.get_total_price()),
                'message': f'{product.name} removed from cart'
            })

        return redirect('cart:detail')


class CartUpdateView(View):
    """Update quantity of a product in cart."""

    def post(self, request, product_id):
        cart = Cart(request)
        product = get_object_or_404(Product, id=product_id)

        form = CartUpdateForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            if quantity > 0:
                cart.update_quantity(product, quantity)
            else:
                cart.remove(product)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            item = cart.get_item(product)
            return JsonResponse({
                'success': True,
                'cart_count': len(cart),
                'cart_total': str(cart.get_total_price()),
                'item_total': str(item['total_price']) if item else '0',
                'quantity': item['quantity'] if item else 0
            })

        return redirect('cart:detail')


class CartClearView(View):
    """Clear all items from the cart."""

    def post(self, request):
        cart = Cart(request)
        cart.clear()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Cart cleared'
            })

        return redirect('cart:detail')


class CartCountView(View):
    """Get cart item count (for AJAX updates)."""

    def get(self, request):
        cart = Cart(request)
        return JsonResponse({
            'count': len(cart),
            'total': str(cart.get_total_price())
        })


class SendTelegramNotificationView(View):
    """Send Telegram notification for completed order (called via AJAX)"""

    def post(self, request, order_id):
        order = get_object_or_404(Order, pk=order_id)

        if order.status != Order.Status.PAID:
            return JsonResponse({
                'success': False,
                'message': 'Order is not paid yet.'
            }, status=400)

        if getattr(order, 'telegram_notification_sent', False):
            return JsonResponse({
                'success': True,
                'message': 'Telegram notification already sent.'
            })

        message = self._format_order_message(order)
        success = self._send_telegram(message)

        if success:
            order.telegram_notification_sent = True
            order.save(update_fields=['telegram_notification_sent'])

        return JsonResponse({
            'success': success,
            'message': 'Notification sent' if success else 'Failed to send'
        })

    def _format_order_message(self, order):
        """Format order message exactly as user specified"""
        from datetime import datetime
        
        # User info
        user_name = order.customer.name or 'Guest'
        user_phone = order.customer.phone or 'N/A'
        user_telegram = order.customer.telegram_phone or 'N/A'
        user_address = order.shipping_address or order.customer.address or 'N/A'
        user_note = order.note or 'None'
        
        # Header
        current_date = datetime.now().strftime('%Y/%m/%d %H:%M')
        message = f"{current_date}\n\n"
        message += "-" * 34 + "\n"
        message += f"Order Code: {order.invoice_no}\n"
        message += "-" * 34 + "\n\n"
        
        # Customer info
        message += f"User: {user_name}\n"
        message += f"Phone: {user_phone}\n"
        message += f"Telegram: {user_telegram}\n"
        message += f"Address: {user_address}\n"
        message += f"Note: {user_note}\n\n"
        
        # Products
        message += "-" * 34 + "\n\n"
        for detail in order.details.all():
            message += f"Product: {detail.product_name}\n"
            message += f"Price: ${detail.price}\n"
            message += f"Qty: {detail.qty}\n"
            # promotion = detail.discount if detail.discount else 0
            # message += f"Promotion: ${promotion}\n\n"
        
        # Total
        message += "-" * 34 + "\n\n"
        message += f"Total: ${order.total}\n"
        
        return message

    def _send_telegram(self, message):
        """Send message to Telegram"""
        from django.conf import settings
        import requests
        
        bot_token = settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.TELEGRAM_CHAT_ID
        topic_id = getattr(settings, 'TELEGRAM_TOPIC_ID', None)
        
        if not bot_token or not chat_id:
            return False
        
        url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        if topic_id:
            payload['message_thread_id'] = topic_id
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            return response.ok
        except:
            return False
