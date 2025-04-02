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


class PasswordChangeForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput)
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password != confirm_password:
            raise forms.ValidationError("새 비밀번호가 일치하지 않습니다.")
        
        return cleaned_data