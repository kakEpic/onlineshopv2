from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    
    # Cart and Order URLs MUST come before products (which has catch-all patterns)
    path('cart/', include('apps.cart.urls', namespace='cart')),
    path('orders/', include('apps.order.urls', namespace='orders')),
    path('payment/', include('apps.payment.urls', namespace='payment')),
    
    # Products URLs (includes catch-all slug pattern)
    path('', include('apps.products.urls')),
    path('products/', include('apps.products.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)