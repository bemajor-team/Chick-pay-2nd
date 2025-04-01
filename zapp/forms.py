# forms.py
from django import forms
from .models import CustomUser
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm

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


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="이메일")  # 기본 username을 email로 표시만 바꾼 것
