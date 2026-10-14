from django import forms
from django.utils.translation import gettext_lazy as _


class CartAddProductForm(forms.Form):
    """Form for adding products to cart."""
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'style': 'width: 80px;'
        })
    )
    override = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.HiddenInput
    )


class CartUpdateForm(forms.Form):
    """Form for updating cart item quantity."""
    quantity = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-sm text-center',
            'style': 'width: 70px;'
        })
    )
