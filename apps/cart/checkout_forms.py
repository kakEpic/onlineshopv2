from django import forms
from django.utils.translation import gettext_lazy as _

from apps.customer.models import Customer


class GuestCheckoutForm(forms.ModelForm):
    """Form for guest checkout - collects customer info."""

    class Meta:
        model = Customer
        fields = ['name', 'phone', 'telegram_phone', 'address', 'note']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Your name'),
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Phone number'),
                'required': True
            }),
            'telegram_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Telegram (optional)')
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Delivery address')
            }),
            'note': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('Order notes (optional)')
            }),
        }


class RegisteredUserCheckoutForm(forms.Form):
    """Form for registered user checkout - uses existing profile."""

    shipping_address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Delivery address')
        }),
        required=True
    )

    note = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': _('Order notes (optional)')
        }),
        required=False
    )
