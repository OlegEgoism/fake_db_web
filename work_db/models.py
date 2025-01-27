from django.contrib.auth.models import AbstractUser
from django.db import models


class Info(models.Model):
    """Информация на сайте"""
    email = models.EmailField(verbose_name="Email", null=True, blank=True)
    github = models.URLField(verbose_name="GitHub", null=True, blank=True)
    vk = models.URLField(verbose_name="ВКонтакте", null=True, blank=True)
    description = models.TextField(verbose_name="Описание", null=True, blank=True)

    def __str__(self):
        return f'Информация на сайте'

    class Meta:
        verbose_name = "Информация на сайте"
        verbose_name_plural = "Информация на сайте"


class CustomUser(AbstractUser):
    """Пользователь"""
    photo = models.ImageField(verbose_name="Фото", upload_to='user_photo/', default='user_photo/default.png', blank=True, null=True)
    phone_number = models.CharField(verbose_name="Телефон", max_length=15, blank=True, null=True)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class DataBaseName(models.Model):
    """Список баз данных"""
    name = models.CharField(verbose_name="Название базы данных", max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Список баз данных"
        verbose_name_plural = "Списки баз данных"
        ordering = 'name',


class DataBaseUser(models.Model):
    """База данных пользователя"""
    db_project = models.CharField(verbose_name="Проект", max_length=200, unique=True)
    db_name = models.CharField(verbose_name="Название", max_length=255)
    db_user = models.CharField(verbose_name="Пользователь", max_length=255)
    db_password = models.CharField(verbose_name="Пароль", max_length=255)
    db_host = models.CharField(verbose_name="Хост", max_length=255)
    db_port = models.CharField(verbose_name="Порт", max_length=8)
    db_date_create = models.DateTimeField(verbose_name="Дата создания проекта", auto_now_add=True)
    user = models.ForeignKey(CustomUser, verbose_name="Пользователь", on_delete=models.CASCADE, related_name='data_base_user')
    data_base_name = models.ForeignKey(DataBaseName, verbose_name="База данных", on_delete=models.CASCADE, related_name='data_base_name')

    def __str__(self):
        return f"Данные БД пользователя: {self.user.username}"

    class Meta:
        verbose_name = "База данных пользователя"
        verbose_name_plural = "Базы данных пользователей"
        ordering = 'user',
