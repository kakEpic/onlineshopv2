from django import forms
from .models import Customer


class CustomerForm(forms.ModelForm):

    class Meta:
        model = Customer
        fields = [
            'name',
            'phone',
            'telegram_phone',
            'address',
        ]

        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'phone': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'telegram_phone': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'address': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}
            ),
        }