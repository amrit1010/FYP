from django import forms
from .models import *
from core.models import CustomUser



class KYCForm(forms.ModelForm):
    class Meta:
        model = KYCVerification
        fields = ['document_number', 'document_image']


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['full_name', 'phone']


