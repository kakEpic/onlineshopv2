from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Product, ProductMedia


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'product_count')
    search_fields = ('name',)

    def product_count(self, obj):
        return obj.products.count()


class ProductMediaInline(admin.TabularInline):
    model = ProductMedia
    extra = 1
    fields = ('media_type', 'file', 'alt_text', 'is_cover', 'display_order')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'barcode', 'category', 'price_display',
        'visibility_badge', 'is_featured', 'is_new_arrival', 'created_at',
    )
    list_filter = (
        'is_visible_to_client', 'is_featured', 'is_new_arrival',
        'category', 'created_at',
    )
    search_fields = ('name', 'handle', 'barcode', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('view_count', 'created_at', 'updated_at', 'created_by')
    inlines = [ProductMediaInline]
    list_per_page = 25
    list_editable = ('is_featured', 'is_new_arrival')

    fieldsets = (
        ('Basic Info (CSV)', {
            'fields': ('handle', 'name', 'slug', 'barcode', 'category', 'description')
        }),
        ('Pricing (CSV)', {
            'fields': (
                ('price_retail', 'retail_sale_type'),
                ('price_wholesale', 'wholesale_sale_type'),
            )
        }),
        ('Discount (Admin)', {
            'fields': ('discount_type', 'discount_price', 'discount_start_date', 'discount_end_date'),
            'description': 'Discount apply លើ retail price តែប៉ុណ្ណោះ',
        }),
        ('Visibility & Flags', {
            'fields': ('is_visible_to_client', 'is_featured', 'is_new_arrival')
        }),
        ('Tracking', {
            'fields': ('view_count', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    @admin.display(description='Retail Price', ordering='price_retail')
    def price_display(self, obj):
        label = f' / {obj.retail_sale_type}' if obj.retail_sale_type else ''
        if obj.is_discount_active:
            return format_html(
                '<span style="text-decoration: line-through; color: gray;">${}</span> '
                '<span style="color: red; font-weight: bold;">${}{}</span> '
                '<span style="color: green; font-size: 10px;">(-{}%)</span>',
                obj.price_retail, obj.discount_price, label, obj.discount_percentage
            )
        return format_html('${}<small style="color: gray;">{}</small>', obj.price_retail, label)

    @admin.display(description='Visible', ordering='is_visible_to_client', boolean=True)
    def visibility_badge(self, obj):
        return obj.is_visible_to_client


@admin.register(ProductMedia)
class ProductMediaAdmin(admin.ModelAdmin):
    list_display = ('product', 'media_type', 'is_cover', 'display_order')
    list_filter = ('media_type', 'is_cover')
    search_fields = ('product__name',)