"""
Products app models
- Category: simple (id + name)
- Product: core fields plus retail/wholesale pricing, sale labels, and discount
- ProductMedia: image and video gallery
"""
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class CategoryQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_deleted=False)

    def deleted(self):
        return self.filter(is_deleted=True)

    def delete(self):
        return self.update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()


class CategoryManager(models.Manager):
    def get_queryset(self):
        return CategoryQuerySet(self.model, using=self._db).filter(is_deleted=False)

    def all_with_deleted(self):
        return CategoryQuerySet(self.model, using=self._db)

    def deleted(self):
        return self.all_with_deleted().deleted()


class Category(models.Model):
    """Product category - simple (id + name)"""
    name = models.CharField(_('name'), max_length=100, unique=True)
    is_deleted = models.BooleanField(_('deleted'), default=False)
    deleted_at = models.DateTimeField(_('deleted at'), null=True, blank=True)

    objects = CategoryManager()
    all_objects = models.Manager()

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.pk and self.name:
            existing = Category.all_objects.filter(name=self.name, is_deleted=True).first()
            if existing:
                self.pk = existing.pk
                self.is_deleted = False
                self.deleted_at = None
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])


class Product(models.Model):
    """
    Product model - core e-commerce entity
    - មាន 2 prices: retail និង wholesale
    - Discount apply លើ retail តែប៉ុណ្ណោះ
    - Sale type labels (Option 1 value ពី CSV) សម្រាប់ display
    """

    # ---------- Basic info (មកពី CSV) ----------
    handle = models.SlugField(
        _('handle'),
        max_length=200,
        unique=True,
        help_text=_('CSV Handle - ID ភ្ជាប់ rows'),
    )
    name = models.CharField(_('name'), max_length=200)
    slug = models.SlugField(_('slug'), max_length=220, unique=True, blank=True)
    description = models.TextField(_('description'), blank=True)
    barcode = models.CharField(_('barcode'), max_length=50, blank=True)

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name=_('category'),
    )

    # ---------- Pricing (មកពី CSV) ----------
    price_retail = models.DecimalField(
        _('retail price'),
        max_digits=10,
        decimal_places=2,
        help_text=_('តម្លៃលក់រាយ (USD)'),
    )
    price_wholesale = models.DecimalField(
        _('wholesale price'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('តម្លៃលក់ដុំ (USD)'),
    )

    # ---------- Sale Type Labels (មកពី CSV: Option 1 value) ----------
    retail_sale_type = models.CharField(
        _('retail sale type'),
        max_length=50,
        blank=True,
        help_text=_('ឧ. "Bottle Retail", "Retail box" - បង្ហាញនៅ product detail'),
    )
    wholesale_sale_type = models.CharField(
        _('wholesale sale type'),
        max_length=50,
        blank=True,
        help_text=_('ឧ. "Bottle WH", "Wholesale box" - បង្ហាញនៅ product detail'),
    )

    # ---------- Discount (Admin set) ----------
    class DiscountType(models.TextChoices):
        FOREVER = 'forever', _('Forever (No Expiry)')
        DATE_RANGE = 'date_range', _('Date Range')

    discount_type = models.CharField(
        _('discount type'),
        max_length=20,
        choices=DiscountType.choices,
        blank=True,
        default='',
        help_text=_('forever = គ្មានកំណត់ | date_range = មានកំណត់ថ្ងៃ'),
    )
    discount_price = models.DecimalField(
        _('discount price'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Discount apply លើ retail price - ទុកទទេបើគ្មាន discount'),
    )
    discount_start_date = models.DateTimeField(
        _('discount start date'),
        null=True,
        blank=True,
    )
    discount_end_date = models.DateTimeField(
        _('discount end date'),
        null=True,
        blank=True,
    )

    # ---------- Visibility & Flags (Admin set) ----------
    is_visible_to_client = models.BooleanField(
        _('visible to client'),
        default=False,
        help_text=_('បង្ហាញឱ្យ client ឃើញ ឬ​ទេ'),
    )
    is_featured = models.BooleanField(
        _('featured'),
        default=False,
        help_text=_('បង្ហាញនៅ homepage'),
    )
    is_new_arrival = models.BooleanField(
        _('new arrival'),
        default=False,
        help_text=_('បង្ហាញ badge "ថ្មី"'),
    )
    is_deleted = models.BooleanField(
        _('deleted'),
        default=False,
        help_text=_('Soft delete flag for product'),
    )
    deleted_at = models.DateTimeField(
        _('deleted at'),
        null=True,
        blank=True,
    )

    # ---------- Tracking ----------
    view_count = models.PositiveIntegerField(_('view count'), default=0)
    total_sold = models.PositiveIntegerField(_('total sold'), default=0)

    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_products',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('product')
        verbose_name_plural = _('products')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_visible_to_client', '-created_at']),
            models.Index(fields=['category', 'is_visible_to_client']),
            models.Index(fields=['handle']),
            models.Index(fields=['barcode']),
        ]

    def __str__(self):
        return self.name

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name, allow_unicode=True) or self.handle
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:detail', kwargs={'slug': self.slug})

    def clean(self):
        super().clean()

        # Normalize discount state
        if self.discount_price is None:
            self.discount_type = ''
            self.discount_start_date = None
            self.discount_end_date = None
        else:
            if not self.discount_type:
                if self.discount_start_date and self.discount_end_date:
                    self.discount_type = self.DiscountType.DATE_RANGE
                else:
                    self.discount_type = self.DiscountType.FOREVER

            if self.discount_type == self.DiscountType.DATE_RANGE:
                if not self.discount_start_date or not self.discount_end_date:
                    raise ValidationError({
                        'discount_start_date': _('ប្រភេទ Date Range ត្រូវកំណត់ Start និង End date។')
                    })

        if self.discount_price is not None:
            if self.discount_price >= self.price_retail:
                raise ValidationError({
                    'discount_price': _('Discount price ត្រូវតូចជាង retail price។')
                })
            if self.discount_price <= 0:
                raise ValidationError({
                    'discount_price': _('Discount price ត្រូវធំជាង 0។')
                })

        if self.discount_start_date and self.discount_end_date:
            if self.discount_end_date <= self.discount_start_date:
                raise ValidationError({
                    'discount_end_date': _('End date ត្រូវធំជាង start date។')
                })

    @property
    def is_discount_active(self):
        """True if discount is currently active (forever OR within date range)."""
        if not self.discount_price:
            return False
        # Forever discount — always active
        if self.discount_type == self.DiscountType.FOREVER:
            return True
        # Date range discount — check dates
        if self.discount_type == self.DiscountType.DATE_RANGE:
            if not self.discount_start_date or not self.discount_end_date:
                return False
            now = timezone.now()
            return self.discount_start_date <= now <= self.discount_end_date
        return False

    @property
    def is_forever_discount(self):
        """True when discount type is forever."""
        return bool(self.discount_price) and self.discount_type == self.DiscountType.FOREVER

    @property
    def final_retail_price(self):
        if self.is_discount_active:
            return self.discount_price
        return self.price_retail

    @property
    def discount_percentage(self):
        """Calculate discount % — works whenever discount_price is set."""
        if not self.discount_price:
            return 0
        return int((self.price_retail - self.discount_price) / self.price_retail * 100)

    @property
    def cover_thumbnail_url(self):
        """
        Returns the best thumbnail URL for this product.
        Priority: cover image > any image > video poster > None
        Used everywhere a static image is needed (cart, orders, lists).
        """
        # 1. Cover image
        cover = self.media.filter(media_type=ProductMedia.MediaType.IMAGE, is_cover=True).first()
        if cover:
            return cover.file.url
        # 2. Any image
        img = self.media.filter(media_type=ProductMedia.MediaType.IMAGE).first()
        if img:
            return img.file.url
        # 3. Video poster (auto-generated thumbnail)
        vid = self.media.filter(
            media_type=ProductMedia.MediaType.VIDEO
        ).exclude(video_poster='').exclude(video_poster=None).first()
        if vid:
            return vid.video_poster.url
        return None

    @property
    def cover_image(self):
        cover = self.media.filter(
            media_type=ProductMedia.MediaType.IMAGE,
            is_cover=True,
        ).first()
        if cover:
            return cover
        return self.media.filter(media_type=ProductMedia.MediaType.IMAGE).first()

    @property
    def cover_video(self):
        """Returns cover video, or first video if none is marked as cover."""
        cover = self.media.filter(
            media_type=ProductMedia.MediaType.VIDEO,
            is_cover=True,
        ).first()
        if cover:
            return cover
        return self.media.filter(media_type=ProductMedia.MediaType.VIDEO).first()

    @property
    def images(self):
        return self.media.filter(media_type=ProductMedia.MediaType.IMAGE)

    @property
    def videos(self):
        return self.media.filter(media_type=ProductMedia.MediaType.VIDEO)


class ProductMedia(models.Model):
    """
    Product Media - រួម Image និង Video
    """

    class MediaType(models.TextChoices):
        IMAGE = 'image', _('Image')
        VIDEO = 'video', _('Video')

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='media',
    )
    media_type = models.CharField(
        _('media type'),
        max_length=10,
        choices=MediaType.choices,
        default=MediaType.IMAGE,
    )
    file = models.FileField(
        _('file'),
        upload_to='products/%Y/%m/',
        help_text=_('Image: jpg, png, webp | Video: mp4, webm'),
    )
    video_poster = models.ImageField(
        _('video poster'),
        upload_to='products/posters/%Y/%m/',
        null=True,
        blank=True,
        help_text=_('Auto-generated thumbnail for video'),
    )
    alt_text = models.CharField(
        _('alt text'),
        max_length=200,
        blank=True,
    )
    is_cover = models.BooleanField(
        _('cover'),
        default=False,
        help_text=_('កំណត់ជារូប/video cover'),
    )
    display_order = models.PositiveIntegerField(_('display order'), default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('product media')
        verbose_name_plural = _('product media')
        ordering = ['-is_cover', 'display_order', 'created_at']

    def __str__(self):
        return f'{self.product.name} - {self.get_media_type_display()} {self.id}'

    def clean(self):
        super().clean()
        if self.file:
            ext = self.file.name.lower().split('.')[-1]
            image_exts = ['jpg', 'jpeg', 'png', 'webp', 'gif']
            video_exts = ['mp4', 'webm', 'mov']

            if self.media_type == self.MediaType.IMAGE and ext not in image_exts:
                raise ValidationError({
                    'file': _(f'Image ត្រូវ​តែ​ជា {", ".join(image_exts)}')
                })
            if self.media_type == self.MediaType.VIDEO and ext not in video_exts:
                raise ValidationError({
                    'file': _(f'Video ត្រូវ​តែ​ជា {", ".join(video_exts)}')
                })

    def save(self, *args, **kwargs):
        if self.is_cover:
            ProductMedia.objects.filter(
                product=self.product,
                media_type=self.media_type,
                is_cover=True,
            ).exclude(pk=self.pk).update(is_cover=False)

        if self.media_type == self.MediaType.IMAGE and not self.is_cover:
            has_cover = ProductMedia.objects.filter(
                product=self.product,
                media_type=self.MediaType.IMAGE,
                is_cover=True,
            ).exclude(pk=self.pk).exists()
            if not has_cover:
                self.is_cover = True

        super().save(*args, **kwargs)