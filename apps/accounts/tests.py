from django.test import TestCase

from .forms import LoginForm
from .models import User


class LoginFormTests(TestCase):
    def test_superuser_can_log_in_with_regular_password(self):
        User.objects.create_superuser(
            username='admin',
            password='admin-password-123',
        )

        form = LoginForm(data={
            'username': 'admin',
            'password': 'admin-password-123',
        })

        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(form.get_user().is_superuser)

    def test_customer_can_log_in_with_six_digit_pin(self):
        User.objects.create_user(username='customer', password='123456')

        form = LoginForm(data={
            'username': 'customer',
            'password': '123456',
        })

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.get_user().username, 'customer')
