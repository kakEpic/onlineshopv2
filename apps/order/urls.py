from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    # ============== Client URLs ==============
    path('my-orders/',
         views.MyOrdersView.as_view(), name='my_orders'),
    path('my-orders/<int:pk>/',
         views.OrderDetailClientView.as_view(), name='client_detail'),

    # Notifications
    path('notifications/',
         views.NotificationListView.as_view(), name='notifications'),
    path('notifications/<int:pk>/read/',
         views.MarkNotificationReadView.as_view(), name='mark_read'),
    path('notifications/read-all/',
         views.MarkAllNotificationsReadView.as_view(), name='mark_all_read'),

    # ============== Dashboard/Admin URLs ==============
    path('dashboard/',
         views.OrderListView.as_view(), name='dashboard_list'),
    path('dashboard/<int:pk>/',
         views.OrderDetailView.as_view(), name='dashboard_detail'),
    path('dashboard/<int:pk>/status/',
         views.OrderStatusUpdateView.as_view(), name='update_status'),
    path('dashboard/create/',
         views.OrderCreateView.as_view(), name='dashboard_create'),
]
