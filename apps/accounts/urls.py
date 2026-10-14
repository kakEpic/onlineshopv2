from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # ---------- Auth ----------
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),
]