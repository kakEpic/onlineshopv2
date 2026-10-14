from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """
    Custom UserManager - uses username to create users
    """
    use_in_migrations = True

    def _create_user(self, username, password, **extra_fields):
        if not username:
            raise ValueError('Username is required')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, password, **extra_fields)

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User Model for e-commerce
    - Login using username and a 6-digit PIN
    - Additional fields: address, phone, telegram
    """

    class Language(models.TextChoices):
        ENGLISH = 'en', _('English')
        KHMER = 'km', _('ខ្មែរ')

    # ---------- Override default fields ----------
    email = models.EmailField(
        _('email address'),
        blank=True,
        null=True,
    )

    # ---------- Custom fields ----------
    phone = models.CharField(
        _('phone number'),
        max_length=20,
        blank=True,
        help_text=_('Format: +855XXXXXXXX or 0XXXXXXXX'),
    )
    address = models.TextField(
        _('address'),
        blank=True,
        help_text=_('Full address'),
    )
    telegram = models.CharField(
        _('telegram username'),
        max_length=100,
        blank=True,
        help_text=_('Telegram username (without @)'),
    )
    security_pin = models.CharField(
        _('security PIN'),
        max_length=6,
        blank=True,
        help_text=_('6-digit PIN for login'),
    )
    preferred_language = models.CharField(
        _('preferred language'),
        max_length=2,
        choices=Language.choices,
        default=Language.KHMER,
    )
    avatar = models.ImageField(
        _('avatar'),
        upload_to='avatars/%Y/%m/',
        blank=True,
        null=True,
    )

    # ---------- Timestamps ----------
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ---------- Configuration ----------
    USERNAME_FIELD = 'username'             # ← Login using username + PIN
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-created_at']

    def __str__(self):
        return self.username or self.email

    def get_full_name(self):
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name or self.username

    def get_short_name(self):
        return self.first_name or self.username