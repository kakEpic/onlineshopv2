from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Order, OrderDetail, Notification


class OrderDetailInline(admin.TabularInline):
    model = OrderDetail
    extra = 0
    readonly_fields = ['line_total']
    fields = ['product', 'product_name', 'price', 'qty', 'discount', 'line_total']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['invoice_no', 'customer', 'status', 'total', 'order_date', 'created_at']
    list_filter = ['status', 'order_date', 'created_at']
    search_fields = ['invoice_no', 'customer__name', 'customer__phone']
    readonly_fields = ['invoice_no', 'total', 'created_at', 'updated_at']
    inlines = [OrderDetailInline]
    ordering = ['-created_at']

    fieldsets = (
        (None, {
            'fields': ('invoice_no', 'customer', 'user', 'status')
        }),
        (_('Details'), {
            'fields': ('order_date', 'shipping_address', 'note')
        }),
        (_('Totals'), {
            'fields': ('total',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OrderDetail)
class OrderDetailAdmin(admin.ModelAdmin):
    list_display = ['order', 'product_name', 'price', 'qty', 'line_total']
    list_filter = ['order__status']
    search_fields = ['product_name', 'order__invoice_no']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'user__email']
    readonly_fields = ['created_at']
