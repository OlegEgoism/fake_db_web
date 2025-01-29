from django.contrib import admin
from django.utils.safestring import mark_safe

from work_db.models import CustomUser, DataBaseName, DataBaseUser, Info

admin.site.site_header = "FAKE DATA"
admin.site.site_title = "Админ-панель FAKE DATA"


class DataBaseUserInline(admin.TabularInline):
    """База данных"""
    model = DataBaseUser
    extra = 0
    classes = ['collapse']
    readonly_fields = 'data_base_name',


@admin.register(Info)
class InfoAdmin(admin.ModelAdmin):
    """Информация на сайте"""
    pass
    list_display = '__str__', 'email', 'github', 'vk', 'short_question',

    def has_add_permission(self, request):
        """Запрещает добавление новых объектов, если достигнут лимит"""
        if Info.objects.count() >= 1:
            return False
        return super().has_add_permission(request)

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
    list_display = 'username', 'preview_photo', 'email', 'phone_number', 'limit_request', 'pay_plan', 'last_login', 'is_active',
    list_filter = 'is_staff', 'is_active', 'date_joined',
    list_editable = 'pay_plan', 'is_active',
    search_fields = 'username', 'email', 'phone_number',
    search_help_text = 'Поиск по имени пользователя, адресу электронной почте и номеру телефона'
    readonly_fields = 'last_login', 'date_joined', 'preview_photo',
    date_hierarchy = 'date_joined'
    inlines = DataBaseUserInline,
    list_per_page = 20

    def preview_photo(self, obj):
        if obj.photo:
            return mark_safe(f'<img src="{obj.photo.url}" width="80" height="80" style="border-radius: 50%;" />')
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


@admin.register(DataBaseName)
class DataBaseNameAdmin(admin.ModelAdmin):
    """База данных"""
    list_display = 'name',
    list_filter = 'name',
    search_fields = 'name', 'db_project',
    search_help_text = 'Поиск по названию базы данных'
    list_per_page = 20


@admin.register(DataBaseUser)
class DataBaseUserAdmin(admin.ModelAdmin):
    """База данных пользователя"""
    list_display = 'db_project', 'user', 'data_base_name', 'db_date_create',
    list_filter = 'data_base_name', 'db_date_create',
    search_fields = 'user__username', 'db_project',
    search_help_text = 'Поиск по логину и названию проекта'
    date_hierarchy = 'db_date_create'
    list_per_page = 20
