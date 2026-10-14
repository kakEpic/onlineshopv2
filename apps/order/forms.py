from django import forms
from django.forms import inlineformset_factory

from .models import (
    Order,
    OrderDetail
)

class OrderForm(forms.ModelForm):

    class Meta:
        model = Order

        fields = [
            'customer',
            'order_date',
            'note'
        ]

        widgets = {
            'customer': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'order_date': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                }
            ),
            'note': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3
                }
            )
        }

class OrderDetailForm(forms.ModelForm):

    class Meta:
        model = OrderDetail

        fields = [
            'product',
            'price',
            'qty',
            'discount'
        ]

        widgets = {
            'product': forms.Select(
                attrs={'class': 'form-select'}
            ),

            'price': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.01'
                }
            ),

            'qty': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.01'
                }
            ),

            'discount': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.01'
                }
            ),
        }

OrderDetailFormSet = inlineformset_factory(
    Order,
    OrderDetail,
    form=OrderDetailForm,
    extra=1,
    can_delete=True
)
