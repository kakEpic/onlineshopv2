from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import User


class LoginForm(AuthenticationForm):
    """
    Login form ប្រើ username និង PIN ៦ ខ្ទង់
    """
    username = forms.CharField(
        label=_('Username'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username',
            'autofocus': True,
        }),
    )
    password = forms.CharField(
        label=_('Password or security PIN'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control text-center',
            'placeholder': _('Enter your password or PIN'),
        }),
    )

    error_messages = {
        'invalid_login': _('Username ឬ password/PIN មិនត្រឹមត្រូវ។'),
        'inactive': _('Account នេះត្រូវបាន disabled។'),
    }


class RegisterForm(forms.ModelForm):
    """
    Registration form - បង្កើត account ថ្មី
    - Username (unique)
    - Security PIN (6 digits only)
    - Address
    - Phone
    - Telegram username
    - Preferred language
    """

    pin1 = forms.CharField(
        label=_('Security PIN'),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control text-center',
            'placeholder': '••••••',
            'maxlength': '6',
            'pattern': '[0-9]{6}',
            'inputmode': 'numeric',
            'style': 'letter-spacing: 0.5em; font-size: 1.5rem;',
            'autocomplete': 'new-password',
        }),
        help_text=_('6-digit number'),
    )
    pin2 = forms.CharField(
        label=_('Confirm PIN'),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control text-center',
            'placeholder': '••••••',
            'maxlength': '6',
            'pattern': '[0-9]{6}',
            'inputmode': 'numeric',
            'style': 'letter-spacing: 0.5em; font-size: 1.5rem;',
            'autocomplete': 'new-password',
        }),
        help_text=_('Confirm PIN'),
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'phone', 'address', 'telegram', 'preferred_language']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter username',
                'autofocus': True,
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last name',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+855 XXXX XXXX or 0XXXXXXXX',
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter full address',
                'rows': 3,
            }),
            'telegram': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Telegram username (without @)',
            }),
            'preferred_language': forms.Select(attrs={
                'class': 'form-select',
            }),
        }

    # ---------- Field-level validation ----------
    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip().lower()
        if not username:
            raise ValidationError(_('Username ត្រូវតែបំពេញ។'))
        if len(username) < 3:
            raise ValidationError(_('Username ត្រូវមាន យ៉ាងហោចណាស់ ៣ តួអក្សរ។'))
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError(_('Username នេះត្រូវបានប្រើរួចហើយ។'))
        return username

    def clean_pin1(self):
        pin = self.cleaned_data.get('pin1', '').strip()
        if not pin:
            raise ValidationError(_('Security PIN ត្រូវតែបំពេញ។'))
        if not pin.isdigit() or len(pin) != 6:
            raise ValidationError(_('PIN ត្រូវតែជាលេខ ៦ ខ្ទង់។'))
        return pin

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone:
            return phone

        # ត្រួតពិនិត្យ format សាមញ្ញ
        if not phone.startswith('+') and not phone.startswith('0'):
            raise ValidationError(_('Phone ត្រូវចាប់ផ្តើមដោយ + ឬ 0'))

        # ត្រួតពិនិត្យថាមានតែលេខ (បន្ទាប់ពី +)
        digits = phone.replace('+', '').replace(' ', '').replace('-', '')
        if not digits.isdigit():
            raise ValidationError(_('Phone ត្រូវមានតែលេខ។'))

        if len(digits) < 8 or len(digits) > 15:
            raise ValidationError(_('Phone ត្រូវមាន ៨-១៥ ខ្ទង់។'))

        return phone

    def clean_telegram(self):
        telegram = self.cleaned_data.get('telegram', '').strip()
        if telegram and telegram.startswith('@'):
            telegram = telegram[1:]
        if telegram and not telegram.replace('_', '').isalnum():
            raise ValidationError(_('Telegram username មិនត្រឹមត្រូវ។'))
        return telegram

    # ---------- Form-level validation ----------
    def clean(self):
        cleaned_data = super().clean()
        pin1 = cleaned_data.get('pin1')
        pin2 = cleaned_data.get('pin2')

        if pin1 and pin2 and pin1 != pin2:
            self.add_error('pin2', _('PIN ទាំងពីរមិនដូចគ្នាទេ។'))

        return cleaned_data

    # ---------- Save ----------
    def save(self, commit=True):
        user = super().save(commit=False)
        # Set PIN as password
        user.set_password(self.cleaned_data['pin1'])
        # Store PIN for reference
        user.security_pin = self.cleaned_data['pin1']

        if commit:
            user.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    """
    Update form for user profile and account details.
    """

    class Meta:
        model = User
        fields = [
            'avatar',
            'username',
            'email',
            'first_name',
            'last_name',
            'phone',
            'telegram',
            'address',
            'preferred_language',
        ]
        widgets = {
            'avatar': forms.ClearableFileInput(attrs={
                'class': 'form-control',
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter username',
                'autofocus': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'name@example.com',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last name',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+855 XXXX XXXX or 0XXXXXXXX',
            }),
            'telegram': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Telegram username (without @)',
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter full address',
                'rows': 3,
            }),
            'preferred_language': forms.Select(attrs={
                'class': 'form-select',
            }),
        }
        labels = {
            'avatar': _('Avatar'),
            'username': _('Username'),
            'email': _('Email'),
            'first_name': _('First Name'),
            'last_name': _('Last Name'),
            'phone': _('Phone'),
            'telegram': _('Telegram'),
            'address': _('Address'),
            'preferred_language': _('Preferred Language'),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip().lower()
        if not username:
            raise ValidationError(_('Username is required.'))
        if len(username) < 3:
            raise ValidationError(_('Username must be at least 3 characters.'))
        if User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists():
            raise ValidationError(_('This username is already taken.'))
        return username

    def clean_telegram(self):
        telegram = self.cleaned_data.get('telegram', '').strip()
        if telegram.startswith('@'):
            telegram = telegram[1:]
        if telegram and not telegram.replace('_', '').isalnum():
            raise ValidationError(_('Telegram username is not valid.'))
        return telegram