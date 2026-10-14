"""
Notification services for cart/checkout.
"""
import logging
import requests
from django.conf import settings
from django.utils.translation import gettext as _
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from apps.order.models import Notification, Order

logger = logging.getLogger(__name__)


def send_websocket_notification(order):
    """
    Send real-time WebSocket notification to admin dashboard.
    """
    try:
        channel_layer = get_channel_layer()
        if channel_layer is None:
            logger.warning('Channel layer not configured')
            return False

        # Get pending orders count
        pending_count = Order.objects.filter(status=Order.Status.PENDING).count()

        # Send to admin notifications group
        async_to_sync(channel_layer.group_send)(
            'admin_notifications',
            {
                'type': 'order_notification',
                'order': {
                    'id': order.id,
                    'invoice_no': order.invoice_no,
                    'customer_name': order.customer.name,
                    'total': str(order.total),
                    'status': order.status,
                    'created_at': order.order_date.isoformat() if order.order_date else None,
                },
                'pending_count': pending_count,
            }
        )
        logger.info(f'WebSocket notification sent for order {order.invoice_no}')
        return True
    except Exception as e:
        logger.error(f'Failed to send WebSocket notification: {e}')
        return False


def send_order_notification(order, user):
    """
    Send in-app notification to user about their order.
    """
    if not user:
        return

    Notification.objects.create(
        user=user,
        notification_type=Notification.NotificationType.ORDER_CREATED,
        title=_('Order Placed Successfully'),
        message=_('Your order #%(invoice)s has been placed and is pending confirmation.') %
                {'invoice': order.invoice_no},
        order=order
    )


def send_order_status_notification(order):
    """
    Send in-app notification when order status changes.
    """
    if not order.user:
        return

    status_messages = {
        'confirmed': (_('Order Confirmed'), _('Your order #%(invoice)s has been confirmed.')),
        'processing': (_('Order Processing'), _('Your order #%(invoice)s is being processed.')),
        'completed': (_('Order Completed'), _('Your order #%(invoice)s has been completed.')),
        'cancelled': (_('Order Cancelled'), _('Your order #%(invoice)s has been cancelled.')),
    }

    if order.status in status_messages:
        title, message = status_messages[order.status]
        notification_type_map = {
            'confirmed': Notification.NotificationType.ORDER_CONFIRMED,
            'completed': Notification.NotificationType.ORDER_COMPLETED,
            'cancelled': Notification.NotificationType.ORDER_CANCELLED,
        }

        Notification.objects.create(
            user=order.user,
            notification_type=notification_type_map.get(
                order.status,
                Notification.NotificationType.SYSTEM
            ),
            title=title,
            message=message % {'invoice': order.invoice_no},
            order=order
        )


def send_telegram_status_update(order):
    """
    Send Telegram notification when order status changes.
    """
    bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', None)
    topic_id = getattr(settings, 'TELEGRAM_TOPIC_ID', None)

    if not bot_token or not chat_id:
        return False

    status_emoji = {
        'pending': '⏳',
        'confirmed': '✅',
        'processing': '🔄',
        'completed': '🎉',
        'cancelled': '❌',
    }

    emoji = status_emoji.get(order.status, '📋')
    message = f"""
{emoji} *Order Status Update*

📋 *Invoice:* `{order.invoice_no}`
📊 *New Status:* {order.get_status_display()}
👤 *Customer:* {order.customer.name}
"""

    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }

    if topic_id:
        payload['message_thread_id'] = topic_id

    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.ok
    except requests.RequestException:
        return False
