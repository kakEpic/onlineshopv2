from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Customer(models.Model):
    """
    Customer model - can be linked to registered user or guest
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customer_profile',
        help_text=_('Link to registered user (null for guests)')
    )
    name = models.CharField(_('name'), max_length=200)
    phone = models.CharField(_('phone'), max_length=30)
    telegram_phone = models.CharField(
        _('telegram'),
        max_length=50,
        blank=True,
        help_text=_('Telegram username or phone')
    )
    address = models.TextField(_('address'), blank=True)
    note = models.TextField(_('note'), blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('customer')
        verbose_name_plural = _('customers')

    def __str__(self):
        return self.name

    @property
    def is_guest(self):
        return self.user is None