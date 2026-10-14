from django.urls import path

from . import views
from .checkout_views import CheckoutView, OrderSuccessView

app_name = 'cart'

urlpatterns = [
    # Cart view
    path('', views.CartDetailView.as_view(), name='detail'),

    # Cart operations
    path('add/<int:product_id>/',
         views.CartAddView.as_view(), name='add'),
    path('remove/<int:product_id>/',
         views.CartRemoveView.as_view(), name='remove'),
    path('update/<int:product_id>/',
         views.CartUpdateView.as_view(), name='update'),
    path('clear/',
         views.CartClearView.as_view(), name='clear'),

    # API
    path('count/',
         views.CartCountView.as_view(), name='count'),
    path('send-telegram/<int:order_id>/',
         views.SendTelegramNotificationView.as_view(), name='send_telegram'),

    # Checkout
    path('checkout/',
         CheckoutView.as_view(), name='checkout'),
    path('order-success/<int:pk>/',
         OrderSuccessView.as_view(), name='order_success'),
]
