from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, DataBaseUser


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")
    photo = forms.ImageField(required=False, label="Фото")

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'photo', 'password1', 'password2')


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

#
# class DataBaseUserForm(forms.ModelForm):
#     """Создать проект базы данных"""
#
#     class Meta:
#         model = DataBaseUser
#         fields = ('data_base_name', 'db_project', 'db_name', 'db_user', 'db_password', 'db_host', 'db_port')
#         widgets = {
#             'data_base_name': forms.Select(attrs={'class': 'form-control'}),
#             'db_project': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите название проекта'}),
#             'db_name': forms.TextInput(attrs={'class': 'form-control'}),
#             'db_user': forms.TextInput(attrs={'class': 'form-control'}),
#             'db_password': forms.PasswordInput(attrs={'class': 'form-control'}),
#             'db_host': forms.TextInput(attrs={'class': 'form-control'}),
#             'db_port': forms.NumberInput(attrs={'class': 'form-control'}),
#         }
