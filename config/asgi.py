"""
ASGI config with Django Channels support for WebSocket notifications.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

# Initialize Django ASGI application early
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from apps.order import routing as order_routing

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(
            order_routing.websocket_urlpatterns
        )
    ),
})