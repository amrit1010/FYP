from django import forms
from .models import *

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input-text input-text--border-radius input-text--primary-style',
                'placeholder': 'Name (Required)',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input-text input-text--border-radius input-text--primary-style',
                'placeholder': 'Email (Required)',
                'required': True
            }),
            'subject': forms.TextInput(attrs={
                'class': 'input-text input-text--border-radius input-text--primary-style',
                'placeholder': 'Subject (Required)',
                'required': True
            }),
            'message': forms.Textarea(attrs={
                'class': 'text-area text-area--border-radius text-area--primary-style',
                'placeholder': 'Compose a Message (Required)',
                'required': True,
                'rows': 5
            }),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Reviews
        fields = ['name', 'email', 'comment']



class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['amount']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'class': 'form-control'})
        }
        labels = {
            'amount': 'Your Bid ($)'
        }

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError("Bid amount must be greater than zero.")
        return amount