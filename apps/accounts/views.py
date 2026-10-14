from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView, UpdateView
from django.contrib.auth.views import LoginView, LogoutView
from django.utils.translation import gettext_lazy as _

from .forms import LoginForm, RegisterForm, ProfileUpdateForm
from .models import User


class UserLoginView(LoginView):
    form_class = LoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()
        messages.success(self.request, f'សូមស្វាគមន៍ {user.username}!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Username ឬ PIN មិនត្រឹមត្រូវ។')
        return super().form_invalid(form)


class UserLogoutView(LogoutView):
    next_page = reverse_lazy('accounts:login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'អ្នកបាន logout ដោយជោគជ័យ។')
        return super().dispatch(request, *args, **kwargs)


class RegisterView(CreateView):
    model = User
    form_class = RegisterForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:profile')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('accounts:profile')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(
            self.request,
            f'សូមស្វាគមន៍ {self.object.username}! Account របស់អ្នកត្រូវបានបង្កើតដោយជោគជ័យ។'
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'សូមកែ errors ខាងក្រោម។')
        return super().form_invalid(form)


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileUpdateForm
    template_name = 'accounts/profile_update.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Your profile has been updated successfully.'))
        return response

    def form_invalid(self, form):
        messages.error(self.request, _('Please correct the errors below.'))
        return super().form_invalid(form)


def logout_view(request):
    logout(request)
    return redirect('products:list')
