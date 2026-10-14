from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'          # ← changed from 'accounts' to 'apps.accounts'
    verbose_name = 'Accounts'