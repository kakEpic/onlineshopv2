from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Product, ProductMedia


class ProductForm(forms.ModelForm):
    """Form for editing products"""
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'category', 'barcode',
            'price_retail', 'price_wholesale',
            'retail_sale_type', 'wholesale_sale_type',
            'discount_type', 'discount_price', 'discount_start_date', 'discount_end_date',
            'is_visible_to_client', 'is_featured', 'is_new_arrival',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control'}),
            'price_retail': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'price_wholesale': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'retail_sale_type': forms.TextInput(attrs={'class': 'form-control'}),
            'wholesale_sale_type': forms.TextInput(attrs={'class': 'form-control'}),
            'discount_type': forms.HiddenInput(),
            'discount_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount_start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'discount_end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'is_visible_to_client': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_new_arrival': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProductMediaForm(forms.ModelForm):
    """Form for uploading product images/videos"""
    
    class Meta:
        model = ProductMedia
        fields = ['media_type', 'file', 'alt_text', 'is_cover']
        widgets = {
            'media_type': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/jpeg,image/png,image/webp,image/gif,video/mp4,video/webm,video/quicktime',
            }),
            'alt_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Alt text for image'}),
            'is_cover': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Max 100MB for videos, 10MB for images
            max_size = 100 * 1024 * 1024 if self.cleaned_data.get('media_type') == 'video' else 10 * 1024 * 1024
            if file.size > max_size:
                max_mb = max_size // (1024 * 1024)
                raise ValidationError(_(f'File ធំ​ពេក (max {max_mb}MB)'))
        return file


class ProductCSVImportForm(forms.Form):
    """Form សម្រាប់ upload CSV/TSV"""

    csv_file = forms.FileField(
        label=_('CSV File'),
        help_text=_(
            'Upload CSV/TSV file - support tab-separated និង comma-separated។ '
            'Columns required: Handle, Option 1 value, Price [Cosvita ]'
        ),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.txt,.tsv',
        }),
    )

    def clean_csv_file(self):
        csv_file = self.cleaned_data.get('csv_file')

        if not csv_file:
            raise ValidationError(_('សូម​ជ្រើស​រើស file'))

        max_size = 10 * 1024 * 1024
        if csv_file.size > max_size:
            raise ValidationError(_('File ធំ​ពេក (max 10MB)'))

        ext = csv_file.name.lower().split('.')[-1]
        if ext not in ['csv', 'txt', 'tsv']:
            raise ValidationError(_('File ត្រូវ​តែ​ជា .csv, .tsv, ឬ .txt'))

        return csv_file