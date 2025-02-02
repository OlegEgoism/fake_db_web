from django.contrib import admin
from django.utils.safestring import mark_safe
from work_db.models import CustomUser, DataBaseName, DataBaseUser, Info, AppSettings, DeletionConfirmation

admin.site.site_header = "FAKE DATA"
admin.site.site_title = "Админ-панель FAKE DATA"


class DataBaseUserInline(admin.TabularInline):
    """База данных"""
    model = DataBaseUser
    extra = 0
    classes = ['collapse']
    readonly_fields = 'data_base_name',


@admin.register(DeletionConfirmation)
class DeletionConfirmationAdmin(admin.ModelAdmin):
    """Коды удаления аккаунтов"""
    list_display = 'user', 'get_user_email', 'code', 'created_at'
    list_filter = 'created_at',
    search_fields = 'code', 'user__username'
    search_help_text = 'Поиск по имени пользователя и коду подтверждения'
    readonly_fields = 'user', 'code', 'created_at',

    def get_user_email(self, obj):
        """Получить email пользователя"""
        return obj.user.email

    get_user_email.short_description = "Почта пользователя"


@admin.register(AppSettings)
class AppSettingsAdmin(admin.ModelAdmin):
    """Информация на сайте"""
    list_display = '__str__', 'limit_create_db', 'connect_timeout_db',

    def has_add_permission(self, request):
        """Запрещает создание новой записи, если уже существует одна запись"""
        return not AppSettings.objects.exists()


@admin.register(Info)
class InfoAdmin(admin.ModelAdmin):
    """Информация на сайте"""
    list_display = '__str__', 'email', 'github', 'vk', 'short_question',

    def has_add_permission(self, request):
        """Запрещает создание новой записи, если уже существует одна запись"""
        return not Info.objects.exists()

    def short_question(self, obj):
        len_str = 100
        if obj.description:
            return obj.description[:len_str] + "..." if len(obj.description) > len_str else obj.description
        return "Информация не заполнена"

    short_question.short_description = 'Описание деятельности'


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    """Пользователь"""
    fieldsets = (
        ('ЛИЧНЫЕ ДАННЫЕ', {
            'fields': ('username', 'preview_photo', 'photo', 'email', 'phone_number', 'limit_request', 'pay_plan', 'last_login', 'date_joined',)},),
        ('РАЗРЕШЕНИЯ', {
            'classes': ('collapse',),
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions',)}),
    )
    list_display = 'username', 'preview_photo', 'email', 'phone_number', 'limit_request', 'db_count',  'pay_plan', 'last_login', 'is_active',
    list_filter = 'pay_plan', 'is_staff', 'is_active', 'date_joined',
    list_editable = 'pay_plan', 'is_active',
    search_fields = 'username', 'email', 'phone_number',
    search_help_text = 'Поиск по имени пользователя, адресу электронной почте и номеру телефона'
    readonly_fields = 'last_login', 'date_joined', 'preview_photo',
    date_hierarchy = 'date_joined'
    inlines = DataBaseUserInline,
    list_per_page = 20

    def preview_photo(self, obj):
        if obj.photo:
            return mark_safe(f'<img src="{obj.photo.url}" width="80" height="80" style="border-radius: 20%;" />')
        else:
            return 'Нет фотографии'

    preview_photo.short_description = 'Фотография'

    def save_model(self, request, obj, form, change):
        """Проверка, есть ли еще один пользователь с таким же адресом электронной почты"""
        if obj.email:
            if CustomUser.objects.filter(email=obj.email).exclude(pk=obj.pk).exists():
                self.message_user(request, "Этот адрес электронной почты уже связан с другим аккаунтом", level='ERROR')
                return
        super().save_model(request, obj, form, change)

    def db_count(self, obj):
        if obj.data_base_user.count() == 0:
            return 'Нет проектов'
        else:
            return obj.data_base_user.count()

    db_count.short_description = 'Количество проектов'


@admin.register(DataBaseName)
class DataBaseNameAdmin(admin.ModelAdmin):
    """База данных"""
    list_display = 'name', 'preview_images_db', 'db_count'
    list_filter = 'name',
    readonly_fields = 'preview_images_db',
    search_fields = 'name', 'db_project',
    search_help_text = 'Поиск по названию базы данных'
    list_per_page = 20

    def preview_images_db(self, obj):
        if obj.images_db:
            return mark_safe(f'<img src="{obj.images_db.url}" width="80" height="80" style="border-radius: 20%;" />')
        else:
            return 'Нет фотографии'

    preview_images_db.short_description = 'Фотография'

    def db_count(self, obj):
        if obj.data_base_name.count() == 0:
            return 'Нет проектов'
        else:
            return obj.data_base_name.count()

    db_count.short_description = 'Количество проектов'


@admin.register(DataBaseUser)
class DataBaseUserAdmin(admin.ModelAdmin):
    """База данных пользователя"""
    list_display = 'db_project', 'user', 'data_base_name', 'db_date_create',
    list_filter = 'data_base_name', 'db_date_create',
    search_fields = 'user__username', 'db_project',
    search_help_text = 'Поиск по логину и названию проекта'
    date_hierarchy = 'db_date_create'
    list_per_page = 20
