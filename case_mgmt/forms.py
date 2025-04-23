# case_mgmt/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Case, CaseFile, DisclosureForm
from django.core.exceptions import ValidationError
import re

class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(choices=CustomUser.ROLES)
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'role', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email']
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Email already exists")
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        
        # Password strength validation
        if len(password1) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        if not re.search(r'[A-Z]', password1):
            raise ValidationError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', password1):
            raise ValidationError("Password must contain at least one lowercase letter")
        if not re.search(r'[0-9]', password1):
            raise ValidationError("Password must contain at least one number")
        if not re.search(r'[^A-Za-z0-9]', password1):
            raise ValidationError("Password must contain at least one special character")
        
        return password2

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class PinataCredentialsForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['pinata_api_key', 'pinata_secret']
        widgets = {
            'pinata_api_key': forms.TextInput(attrs={'placeholder': 'Pinata API Key'}),
            'pinata_secret': forms.PasswordInput(attrs={'placeholder': 'Pinata Secret API Key'}),
        }

class CaseForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = ['case_type', 'name', 'case_number', 'description', 'status', 'location']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class CaseFileForm(forms.Form):
    file = forms.FileField()

class ShareCaseForm(forms.Form):
    email = forms.EmailField()

class DisclosureFormForm(forms.ModelForm):
    class Meta:
        model = DisclosureForm
        fields = ['form_name']