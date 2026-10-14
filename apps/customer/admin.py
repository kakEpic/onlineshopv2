from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'telegram_phone', 'user', 'is_guest', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'phone', 'telegram_phone', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'is_guest']
    ordering = ['-created_at']

    fieldsets = (
        (None, {
            'fields': ('user', 'name', 'phone', 'telegram_phone')
        }),
        (_('Address'), {
            'fields': ('address', 'note')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
