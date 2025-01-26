from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, DataBaseUser


class CustomUserCreationForm(UserCreationForm):
    photo = forms.ImageField(required=False)
    phone_number = forms.CharField(max_length=15, required=False)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone_number', 'photo', 'password1', 'password2')


class DataBaseUserForm(forms.ModelForm):
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


