"""
WebSocket consumers for real-time order notifications.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async


class OrderNotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for admin dashboard order notifications.
    Sends real-time notifications when new orders are placed.
    """

    async def connect(self):
        """Handle WebSocket connection."""
        # Check if user is staff/admin
        user = self.scope.get('user')
        if user and user.is_authenticated and user.is_staff:
            # Join the admin notifications group
            self.group_name = 'admin_notifications'
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
            
            # Send initial pending order count
            pending_count = await self.get_pending_orders_count()
            await self.send(text_data=json.dumps({
                'type': 'init',
                'pending_count': pending_count,
            }))
        else:
            await self.close()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'get_count':
                pending_count = await self.get_pending_orders_count()
                await self.send(text_data=json.dumps({
                    'type': 'count_update',
                    'pending_count': pending_count,
                }))
            elif action == 'mark_seen':
                order_id = data.get('order_id')
                if order_id:
                    await self.mark_order_as_seen(order_id)
        except json.JSONDecodeError:
            pass

    async def order_notification(self, event):
        """Handle order notification event from channel layer."""
        await self.send(text_data=json.dumps({
            'type': 'new_order',
            'order': event['order'],
            'pending_count': event['pending_count'],
        }))

    async def order_count_update(self, event):
        """Handle order count update event."""
        await self.send(text_data=json.dumps({
            'type': 'count_update',
            'pending_count': event['pending_count'],
        }))

    @database_sync_to_async
    def get_pending_orders_count(self):
        """Get count of pending orders."""
        from apps.order.models import Order
        return Order.objects.filter(status=Order.Status.PENDING).count()

    @database_sync_to_async
    def mark_order_as_seen(self, order_id):
        """Mark order notification as seen."""
        from apps.order.models import Order
        try:
            order = Order.objects.get(id=order_id)
            order.admin_notified = True
            order.save(update_fields=['admin_notified'])
        except Order.DoesNotExist:
            pass
