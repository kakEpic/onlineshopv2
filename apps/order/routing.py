"""
WebSocket URL routing for order notifications.
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/notifications/$', consumers.OrderNotificationConsumer.as_asgi()),
]
