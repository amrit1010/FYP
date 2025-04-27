from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(required=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'phone', 'password1', 'password2']