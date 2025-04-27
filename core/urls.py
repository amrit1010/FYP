from django.urls import path
from .views import *

app_name = 'core'

urlpatterns = [
    path('login/', user_login, name='login'),
    path('register/', register, name='register'),
    path('activate/<uidb64>/<token>/', activate, name='activate'),

    path('forgot-password/', forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/',reset_password, name='reset_password'),
    path('check-mail/', check_mail, name='check_mail'),

    path('check_email/', check_email, name='check_email'),
    path('logout/', user_logout, name='logout'),
    path('dashboard/', dashboard_redirect, name='dashboard_redirect'),
]