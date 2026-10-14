from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'phone', 'telegram', 'is_staff', 'created_at')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'preferred_language')
    search_fields = ('username', 'first_name', 'last_name', 'phone', 'telegram', 'email')
    ordering = ('-created_at',)

    fieldsets = (
        (None, {'fields': ('username', 'password', 'security_pin')}),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'phone', 'address', 'avatar', 'email')
        }),
        (_('Contact'), {
            'fields': ('telegram', 'preferred_language')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'security_pin', 'password1', 'password2'),
        }),
        (_('Personal info'), {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'email', 'phone', 'address', 'telegram'),
        }),
    )

    readonly_fields = ('last_login', 'date_joined', 'created_at', 'updated_at')