from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Sum, F
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Order(models.Model):
    """
    Order model with status tracking
    """

    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        PAID = 'paid', _('Paid')
        CONFIRMED = 'confirmed', _('Confirmed')
        PROCESSING = 'processing', _('Processing')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')

    invoice_no = models.CharField(
        _('invoice number'),
        max_length=30,
        unique=True,
        editable=False
    )

    customer = models.ForeignKey(
        'customer.Customer',
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name=_('customer')
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        help_text=_('Registered user who placed the order')
    )

    status = models.CharField(
        _('status'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    order_date = models.DateTimeField(
        _('order date'),
        default=timezone.now
    )

    shipping_address = models.TextField(
        _('shipping address'),
        blank=True
    )

    note = models.TextField(
        _('note'),
        blank=True
    )

    total = models.DecimalField(
        _('total'),
        max_digits=18,
        decimal_places=2,
        default=Decimal('0.00')
    )

    khqr = models.TextField(_('Bakong QR payload'), blank=True)
    qr_image = models.TextField(_('QR image data'), blank=True)
    md5 = models.CharField(_('QR MD5'), max_length=100, blank=True)
    telegram_notification_sent = models.BooleanField(
        _('telegram notification sent'),
        default=False,
        help_text=_('Set to true once the order success Telegram notification has been sent.')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('order')
        verbose_name_plural = _('orders')

    def save(self, *args, **kwargs):
        if not self.invoice_no:
            today = timezone.now().strftime('%Y%m%d')
            last_order = Order.objects.filter(
                invoice_no__startswith=today
            ).order_by('-id').first()

            seq = 1
            if last_order:
                seq = int(last_order.invoice_no.split('-')[-1]) + 1

            self.invoice_no = f"{today}-{str(seq).zfill(3)}"

        super().save(*args, **kwargs)

    def calculate_total(self):
        """Calculate and save total from order details"""
        total = self.details.aggregate(
            total=Sum(F('price') * F('qty') - F('discount'))
        )['total'] or Decimal('0')
        self.total = total
        self.save(update_fields=['total'])
        return total

    @property
    def subtotal(self):
        total = self.details.aggregate(
            total=Sum(F('price') * F('qty') - F('discount'))
        )
        return total['total'] or Decimal('0')

    @property
    def grand_total(self):
        return self.subtotal

    def get_absolute_url(self):
        return reverse('orders:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.invoice_no

class OrderDetail(models.Model):
    """
    Order line items
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='details',
        verbose_name=_('order')
    )

    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        verbose_name=_('product')
    )

    product_name = models.CharField(
        _('product name'),
        max_length=200,
        help_text=_('Snapshot of product name at time of order')
    )

    price = models.DecimalField(
        _('price'),
        max_digits=18,
        decimal_places=2
    )

    qty = models.PositiveIntegerField(
        _('quantity'),
        default=1
    )

    discount = models.DecimalField(
        _('discount'),
        max_digits=18,
        decimal_places=2,
        default=Decimal('0.00')
    )

    class Meta:
        ordering = ['id']
        verbose_name = _('order detail')
        verbose_name_plural = _('order details')

    @property
    def line_total(self):
        return (self.price * self.qty) - self.discount

    @property
    def subtotal(self):
        return self.price * self.qty

    def save(self, *args, **kwargs):
        # Save product name snapshot
        if not self.product_name and self.product:
            self.product_name = self.product.name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_name} x {self.qty}"


class Notification(models.Model):
    """
    In-app notification system
    """

    class NotificationType(models.TextChoices):
        ORDER_CREATED = 'order_created', _('Order Created')
        ORDER_CONFIRMED = 'order_confirmed', _('Order Confirmed')
        ORDER_COMPLETED = 'order_completed', _('Order Completed')
        ORDER_CANCELLED = 'order_cancelled', _('Order Cancelled')
        SYSTEM = 'system', _('System')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('user')
    )

    notification_type = models.CharField(
        _('type'),
        max_length=30,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM
    )

    title = models.CharField(_('title'), max_length=200)
    message = models.TextField(_('message'))

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name=_('related order')
    )

    is_read = models.BooleanField(_('read'), default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')

    def __str__(self):
        return self.title

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])