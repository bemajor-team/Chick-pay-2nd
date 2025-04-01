# forms.py
from django import forms
from .models import CustomUser
from django.contrib.auth.forms import UserCreationForm

class RegisterForm(UserCreationForm):
    name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    birthdate = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True
    )

    class Meta:
        model = CustomUser
        fields = ['name', 'email', 'birthdate', 'password1', 'password2']
