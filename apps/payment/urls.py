from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    path('order/<int:pk>/', views.OrderPaymentView.as_view(), name='order_payment'),
    path('order/<int:pk>/check/', views.CheckPaymentStatusView.as_view(), name='check_payment'),
    path('order/<int:pk>/success/', views.OrderPaymentSuccessView.as_view(), name='payment_success'),
]
