from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import CustomUser, DataBaseUser



class CustomUserCreationForm(UserCreationForm):
    """Регистрация пользователя"""
    email = forms.EmailField(required=True, label="Email")
    photo = forms.ImageField(required=False, label="Фото")

    class Meta:
        model = CustomUser
        fields = 'username', 'email', 'photo', 'password1', 'password2'
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким email уже зарегистрирован.")
        return email


class CustomUserForm(forms.ModelForm):
    """Редактирование профиля пользователя"""

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone_number', 'photo']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }


class DataBaseUserForm(forms.ModelForm):
    """Редактирование данных проекта"""

    class Meta:
        model = DataBaseUser
        fields = ('data_base_name', 'db_project', 'db_name', 'db_user', 'db_password', 'db_host', 'db_port')
        widgets = {
            'data_base_name': forms.Select(attrs={'class': 'form-control'}),
            'db_project': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите название проекта'}),
            'db_name': forms.TextInput(attrs={'class': 'form-control'}),
            'db_user': forms.TextInput(attrs={'class': 'form-control'}),
            'db_password': forms.PasswordInput(attrs={'class': 'form-control'}),
            'db_host': forms.TextInput(attrs={'class': 'form-control'}),
            'db_port': forms.NumberInput(attrs={'class': 'form-control'}),
        }



