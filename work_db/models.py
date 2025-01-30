from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models


class AppSettings(models.Model):
    """Настройки проекта"""
    limit_create_db = models.IntegerField(verbose_name="Лимит создания проектов", default=3)
    connect_timeout_db = models.IntegerField(verbose_name="Время проверки соединения в БД", default=5)

    def __str__(self):
        return f'Настройки проекта'

    class Meta:
        verbose_name = "Настройки проекта"
        verbose_name_plural = "Настройки проекта"


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
    pay_plan = models.BooleanField(verbose_name="Расширенный доступ", default=False)
    limit_request = models.IntegerField(verbose_name="Лимит строк генерации данных", default=10000000)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class DeletionConfirmation(models.Model):
    """Коды удаления аккаунтов"""
    user = models.OneToOneField(CustomUser, verbose_name="Пользователь", on_delete=models.CASCADE, related_name='deletion_code')
    code = models.CharField(verbose_name="Код подтверждения", max_length=6)
    created_at = models.DateTimeField(verbose_name="Дата отправки кода на почту", auto_now_add=True)

    def __str__(self):
        return f"Код удаления для f{self.user.username}"

    class Meta:
        verbose_name = "Код удаления аккаунта"
        verbose_name_plural = "Коды удаления аккаунтов"


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
    """Проект пользователя"""
    db_project = models.CharField(verbose_name="Проект", max_length=200, unique=True)
    db_name = models.CharField(verbose_name="Название", max_length=255)
    db_user = models.CharField(verbose_name="Пользователь", max_length=255)
    db_password = models.CharField(verbose_name="Пароль", max_length=255)
    db_host = models.CharField(verbose_name="Хост", max_length=255)
    db_port = models.CharField(verbose_name="Порт", max_length=8)
    db_date_create = models.DateTimeField(verbose_name="Дата создания проекта", auto_now_add=True)
    db_date_edit = models.DateTimeField(verbose_name="Дата изменения", auto_now=True)
    user = models.ForeignKey(CustomUser, verbose_name="Пользователь", on_delete=models.CASCADE, related_name='data_base_user')
    data_base_name = models.ForeignKey(DataBaseName, verbose_name="База данных", on_delete=models.CASCADE, related_name='data_base_name')

    def __str__(self):
        return f"Данные БД пользователя: {self.user.username}"

    class Meta:
        verbose_name = "Проект пользователя"
        verbose_name_plural = "Проекты пользователей"
        ordering = 'db_date_create',
