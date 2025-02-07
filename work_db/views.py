import csv
import random
import psycopg2
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail, EmailMessage
from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import login
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from faker import Faker
from .data.data_choices_list import choices_list
from .data.db_connection import get_db_connection
from .forms import CustomUserCreationForm, DataBaseUserForm, CustomUserForm
from django.contrib import messages
from django.contrib.auth import logout
from .models import Info, DataBaseUser, AppSettings, DeletionConfirmation
from django.contrib.auth import get_user_model
import pyjokes

User = get_user_model()


def home(request):
    """Главная"""
    info = Info.objects.first()
    return render(request, template_name='home.html', context={
        'info': info
    })


def about_us(request):
    """Страница о нас"""
    info = Info.objects.first()
    return render(request, template_name='about_us.html', context={
        'info': info
    })


# TODO
@login_required
def profile(request):
    """Страница профиля пользователя"""
    info = Info.objects.first()
    user_databases = DataBaseUser.objects.filter(user=request.user)
    return render(request, template_name='profile.html', context={
        'info': info,
        'user': request.user,
        'user_databases': user_databases
    })


@login_required
def edit_profile(request):
    """Редактирование профиля пользователя"""
    info = Info.objects.first()
    user = request.user
    if request.method == 'POST':
        form = CustomUserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль успешно обновлен.")
            return redirect('profile')
        else:
            messages.error(request, "Ошибка при обновлении профиля. Проверьте введенные данные.")
    else:
        form = CustomUserForm(instance=user)
    return render(request, template_name='edit_profile.html', context={
        'info': info,
        'form': form
    })


def register(request):
    """Регистрация пользователя с подтверждением по email"""
    info = Info.objects.first()
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            mail_subject = "Подтвердите ваш email"
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            confirm_link = f"http://{current_site.domain}/verify-email/{uid}/{token}/"
            html_message = render_to_string(template_name="registration/verify_email.html", context={
                "user": user,
                "confirm_link": confirm_link
            })
            email = EmailMessage(
                subject=mail_subject,
                body=html_message,
                from_email=settings.EMAIL_HOST_USER,
                to=[user.email]
            )
            email.content_subtype = "html"
            email.send()
            return render(request, template_name="registration/registration_pending.html")
    else:
        form = CustomUserCreationForm()
    return render(request, template_name="registration/register.html", context={
        "info": info,
        "form": form
    })


def verify_email(request, uidb64, token):
    """Подтверждение email"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        if user and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            login(request, user)
            return redirect("home")
        else:
            return render(request, template_name="registration/invalid_verification.html")
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return render(request, template_name="registration/invalid_verification.html")


@login_required
def request_account_deletion(request):
    """Запрос на удаление аккаунта с отправкой кода подтверждения"""
    user = request.user
    code = str(random.randint(100000, 999999))
    deletion_code, created = DeletionConfirmation.objects.get_or_create(user=user)
    deletion_code.code = code
    deletion_code.save()
    send_mail(
        subject="Подтверждение удаления аккаунта",
        message=f"Ваш код для удаления аккаунта: {code}",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.email],
        fail_silently=False,
    )
    messages.success(request, "Код подтверждения отправлен на вашу почту.")
    return redirect("confirm_account_deletion")


@login_required
def confirm_account_deletion(request):
    """Подтверждение удаления аккаунта"""
    user = request.user
    if request.method == "POST":
        entered_code = request.POST.get("code")
        try:
            deletion_code = DeletionConfirmation.objects.get(user=user)
        except DeletionConfirmation.DoesNotExist:
            messages.error(request, "Ошибка! Код не найден. Запросите новый.")
            return redirect("request_account_deletion")
        if entered_code == deletion_code.code:
            user.delete()
            messages.success(request, "Ваш аккаунт успешно удален.")
            return redirect("home")
        else:
            messages.error(request, "Неверный код подтверждения. Попробуйте еще раз.")
    return render(request, template_name="confirm_account_deletion.html")


def logout_view(request):
    """Выход пользователя"""
    logout(request)
    return redirect('home')


# TODO
@login_required
def database_detail(request, pk):
    """Страница информации о конкретной базе данных пользователя"""
    database = get_object_or_404(DataBaseUser, pk=pk)
    return render(request, template_name='database_detail.html', context={
        'database': database
    })


@login_required
def database_edit(request, pk):
    """Редактирование информации о базе данных и проверка подключения"""
    info = Info.objects.first()
    connect_timeout = AppSettings.objects.first().connect_timeout_db
    database = get_object_or_404(DataBaseUser, pk=pk)
    if request.method == 'POST':
        form = DataBaseUserForm(request.POST, instance=database)
        if form.is_valid():
            database = form.save(commit=False)
            if not form.cleaned_data['db_password']:
                database.db_password = DataBaseUser.objects.get(pk=pk).db_password
            database.save()
            if 'check_connection' in request.POST:
                try:
                    connection = psycopg2.connect(
                        dbname=database.db_name,
                        user=database.db_user,
                        password=database.db_password,
                        host=database.db_host,
                        port=database.db_port,
                        connect_timeout=connect_timeout
                    )
                    messages.success(request, f"Успешное подключение к базе данных '{database.db_name}'.", extra_tags="alert alert-success")
                    connection.close()
                except psycopg2.OperationalError:
                    messages.error(request, "Ошибка подключения! Проверьте настройки подключения.", extra_tags="alert alert-danger")
                except Exception as e:
                    messages.error(request, f"Ошибка подключения: {str(e)}", extra_tags="alert alert-danger")
            else:
                messages.success(request, "Данные успешно сохранены.", extra_tags="alert alert-success")
        else:
            messages.error(request, message="")
    else:
        form = DataBaseUserForm(instance=database)
        form.fields['db_password'].widget.attrs['value'] = database.db_password
    return render(request, template_name='database_edit.html', context={
        'info': info,
        'form': form,
        'database': database
    })


@login_required
def database_delete(request, pk):
    """Удаление проекта базы данных"""
    database = get_object_or_404(DataBaseUser, pk=pk)
    database.delete()
    messages.success(request, 'Проект успешно удален.')
    return redirect('my_projects')


@login_required
def create_project(request):
    """Создать проект базы данных"""
    info = Info.objects.first()
    limit_create_db = AppSettings.objects.first().limit_create_db
    user = request.user
    if not user.pay_plan:
        user_projects_count = DataBaseUser.objects.filter(user=user).count()
        if user_projects_count >= limit_create_db:
            messages.error(request, f"Вы достигли лимита в {limit_create_db} проекта. Для создания большего количества проектов обновите план.", extra_tags="alert alert-warning")
            return redirect('my_projects')
    if request.method == 'POST':
        form = DataBaseUserForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.user = user
            project.save()
            messages.success(request, "Проект успешно создан!", extra_tags="alert alert-success")
            return redirect('my_projects')
    else:
        form = DataBaseUserForm()
    return render(request, template_name='create_project.html', context={
        'info': info,
        'form': form
    })


@login_required
def my_projects(request):
    """Мои проекты базы данных"""
    info = Info.objects.first()
    projects = DataBaseUser.objects.filter(user=request.user).order_by('db_date_create')
    return render(request, template_name='my_projects.html', context={
        'info': info,
        'projects': projects
    })


@login_required
def connect_to_database(request, pk):
    """Проверяет подключение к базе данных."""
    info = Info.objects.first()
    project = get_object_or_404(DataBaseUser, pk=pk)
    connection, error_message = get_db_connection(project)
    connection_status = f"Успешное подключение к базе '{project.db_name}'" if connection else None
    if connection:
        connection.close()
    return render(request, template_name='connect_result.html', context={
        'info': info,
        'project': project,
        'connection_status': connection_status,
        'error_message': error_message
    })


@login_required
def database_schemas(request, pk):
    """Получает список схем в базе данных."""
    info = Info.objects.first()
    project = get_object_or_404(DataBaseUser, pk=pk)
    schemas, error_message = [], None
    connection, error_message = get_db_connection(project)
    if connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name NOT IN ('pg_toast', 'pg_catalog', 'information_schema')
                ORDER BY schema_name;
            """)
            schemas = [row[0] for row in cursor.fetchall()]
        connection.close()
    return render(request, template_name='database_schemas.html', context={
        'info': info,
        'project': project,
        'schemas': schemas,
        'error_message': error_message
    })


@login_required
def schema_tables(request, pk, schema_name):
    """Получает список таблиц в схеме."""
    info = Info.objects.first()
    project = get_object_or_404(DataBaseUser, pk=pk)
    tables, error_message = [], None
    connection, error_message = get_db_connection(project)
    if connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s;
            """, (schema_name,))
            tables = [row[0] for row in cursor.fetchall()]
        connection.close()
    return render(request, template_name='schema_tables.html', context={
        'info': info,
        'project': project,
        'schema_name': schema_name,
        'tables': tables,
        'error_message': error_message
    })


@login_required
def table_columns(request, pk, schema_name, table_name):
    """Получает информацию о колонках таблицы и количестве записей."""
    info = Info.objects.first()
    project = get_object_or_404(DataBaseUser, pk=pk)
    columns, record_count, error_message = [], 0, None
    connection, error_message = get_db_connection(project)
    if connection:
        with connection.cursor() as cursor:
            if request.method == 'POST' and 'clear_table' in request.POST:
                cursor.execute(f'TRUNCATE TABLE "{schema_name}"."{table_name}" RESTART IDENTITY CASCADE;')
                connection.commit()
            cursor.execute("""
                SELECT 
                    column_name, 
                    data_type, 
                    COALESCE(
                        (SELECT pg_catalog.col_description(c.oid, cols.ordinal_position::int)), 
                        'Нет описания'
                    ) AS column_comment
                FROM information_schema.columns cols
                JOIN pg_catalog.pg_class c ON c.relname = cols.table_name
                WHERE cols.table_schema = %s 
                  AND cols.table_name = %s;
            """, (schema_name, table_name))
            columns = cursor.fetchall()
            cursor.execute(f'SELECT COUNT(*) FROM "{schema_name}"."{table_name}";')
            record_count = cursor.fetchone()[0]
        connection.close()
    return render(request, template_name='table_columns.html', context= {
        'info': info,
        'project': project,
        'schema_name': schema_name,
        'table_name': table_name,
        'columns': columns,
        'record_count': record_count,
        'error_message': error_message
    })


def generate_fake_value(column_name, selected_value, fake):
    """Генерирует случайное значение в зависимости от выбранного типа данных"""
    if selected_value == 'ФИО':
        return fake.name()
    elif selected_value == 'Фамилия':
        return fake.last_name()
    elif selected_value == 'Имя':
        return fake.first_name()
    elif selected_value == 'Отчество':
        return fake.middle_name()
    elif selected_value == 'Логин':
        return fake.user_name()
    elif selected_value == 'Дата рождения':
        return fake.date_of_birth(minimum_age=18, maximum_age=90)
    elif selected_value == 'Возраст':
        return fake.random_int(min=18, max=90)
    elif selected_value == 'Пол':
        return fake.random_element(['Мужской', 'Женский'])
    elif selected_value == 'Страна':
        return fake.country()
    elif selected_value == 'Город':
        return fake.city()
    elif selected_value == 'Адрес':
        return fake.street_address()
    elif selected_value == 'Почтовый индекс':
        return fake.postcode()
    elif selected_value == 'Email':
        return fake.unique.email()
    elif selected_value == 'Телефон':
        return fake.phone_number()
    elif selected_value == 'Широта':
        return fake.latitude()
    elif selected_value == 'Долгота':
        return fake.longitude()
    elif selected_value == 'Компания':
        return fake.company()
    elif selected_value == 'Категория продукта':
        return fake.word(ext_word_list=['Электроника', 'Книги', 'Одежда', 'Игрушки', 'Мебель', 'Транспорт'])
    elif selected_value == 'Должность':
        return fake.job()
    elif selected_value == 'Отдел':
        return fake.bs()
    elif selected_value == 'Валюта':
        return fake.currency_name()
    elif selected_value == 'Символ валюты':
        return fake.currency_symbol()
    elif selected_value == 'Кредитная карта':
        return fake.credit_card_number()
    elif selected_value == 'IBAN':
        return fake.iban()
    elif selected_value == 'Случайный текст (до 100 букв)':
        return fake.text()
    elif selected_value == 'Заголовок':
        return fake.catch_phrase()
    elif selected_value == 'Рейтинг (1-5)':
        return fake.random_int(min=1, max=5)
    elif selected_value == 'Цена':
        return fake.random_number(digits=5)
    elif selected_value == 'Цвет':
        return fake.color_name()
    elif selected_value == 'Пароль':
        return fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
    elif selected_value == 'IP-адрес':
        return fake.ipv4()
    elif selected_value == 'Домен':
        return fake.domain_name()
    elif selected_value == 'URL':
        return fake.url()
    elif selected_value == 'URI':
        return fake.uri()
    elif selected_value == 'UUID':
        return fake.uuid4()
    elif selected_value == 'Число (большое)':
        return fake.random_int(min=1, max=9000000)
    elif selected_value == 'True/False':
        return fake.boolean()
    elif selected_value == 'Случайный хэш':
        return fake.sha256()
    elif selected_value == 'JSON-объект':
        return fake.json()
    elif selected_value == 'Дата':
        return fake.date()
    elif selected_value == 'Время':
        return fake.time()
    elif selected_value == 'Дата и время':
        return fake.date_time()
    elif selected_value == 'Временная зона':
        return fake.timezone()
    elif selected_value == 'Дата в прошлом':
        return fake.past_date()
    elif selected_value == 'Дата в будущем':
        return fake.future_date()
    else:
        return None  # По умолчанию, если тип данных неизвестен


@login_required
def generate_fake_data(request, pk, schema_name, table_name):
    """Генерация случайных данных для указанной таблицы"""
    info = Info.objects.first()
    project = get_object_or_404(DataBaseUser, pk=pk)
    user = project.user
    fake = Faker('ru_RU')
    error_message, inserted_rows, record_count, retry_attempts = None, 0, 0, 200
    data_choices = choices_list
    connection, error_message = get_db_connection(project)

    try:
        cursor = connection.cursor()
        cursor.execute(f'SELECT COUNT(*) FROM "{schema_name}"."{table_name}";')
        record_count = cursor.fetchone()[0]
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = %s 
              AND table_name = %s;
        """, (schema_name, table_name))
        columns = cursor.fetchall()
        column_data = [
            {
                'name': col[0],
                'type': col[1],
                'choices': data_choices.get(col[1], ['Произвольное значение'])
            }
            for col in columns
        ]
        cursor.close()
        connection.close()
    except Exception as e:
        error_message = f"Ошибка подключения: {str(e)}"

    if request.method == 'POST':
        num_records = int(request.POST.get('num_records', 10))

        if not user.pay_plan and user.limit_request < num_records:
            error_message = f"Превышен лимит запросов. Доступно: {user.limit_request}"
            return render(request, template_name='generate_fake_data.html', context={
                'project': project,
                'schema_name': schema_name,
                'table_name': table_name,
                'inserted_rows': inserted_rows,
                'record_count': record_count,
                'error_message': error_message
            })

        try:
            connection = psycopg2.connect(
                dbname=project.db_name,
                user=project.db_user,
                password=project.db_password,
                host=project.db_host,
                port=project.db_port
            )
            cursor = connection.cursor()
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = %s 
                  AND table_name = %s;
            """, (schema_name, table_name))
            columns = cursor.fetchall()
            column_data = [{'name': col[0], 'type': col[1]} for col in columns]

            column_names = [f'"{col["name"]}"' for col in column_data]  # SQL-кавычки
            placeholders = ', '.join(['%s' for _ in column_data])
            insert_query = f'INSERT INTO "{schema_name}"."{table_name}" ({", ".join(column_names)}) VALUES ({placeholders})'

            for _ in range(num_records):
                attempt = 0
                while attempt < retry_attempts:
                    values = [
                        generate_fake_value(col["name"], request.POST.get(f'column_{col["name"]}', 'Произвольное значение'), fake)
                        for col in column_data
                    ]

                    try:
                        cursor.execute(insert_query, values)
                        inserted_rows += 1
                        break  # Успешная вставка, выход из цикла
                    except psycopg2.IntegrityError:
                        connection.rollback()
                        attempt += 1
                        if attempt == retry_attempts:
                            raise

            connection.commit()
            cursor.execute(f'SELECT COUNT(*) FROM "{schema_name}"."{table_name}";')
            record_count = cursor.fetchone()[0]
            cursor.close()
            connection.close()

            if not user.pay_plan:
                user.limit_request = max(0, user.limit_request - num_records)
                user.save()

        except psycopg2.IntegrityError as e:
            error_message = f"Ошибка вставки данных (дубликат): {str(e)}"
        except Exception as e:
            error_message = f"Ошибка вставки данных: {str(e)}"

    return render(request, template_name='generate_fake_data.html', context={
        'info': info,
        'project': project,
        'schema_name': schema_name,
        'table_name': table_name,
        'column_data': column_data,
        'inserted_rows': inserted_rows,
        'record_count': record_count,
        'error_message': error_message,
    })


# @login_required
# def generate_fake_data(request, pk, schema_name, table_name):
#     """Генерация случайных данных для указанной таблицы"""
#     info = Info.objects.first()
#     project = get_object_or_404(DataBaseUser, pk=pk)
#     user = project.user
#     fake = Faker('ru_RU')
#     error_message, inserted_rows, record_count, retry_attempts = None, 0, 0 ,200
#     data_choices = choices_list
#     connection, error_message = get_db_connection(project)
#     try:
#         connection = connection
#         cursor = connection.cursor()
#         cursor.execute(f'SELECT COUNT(*) FROM "{schema_name}"."{table_name}";')
#         record_count = cursor.fetchone()[0]
#         cursor.execute("""
#             SELECT column_name, data_type
#             FROM information_schema.columns
#             WHERE table_schema = %s
#               AND table_name = %s;
#         """, (schema_name, table_name))
#         columns = cursor.fetchall()
#         column_data = [
#             {
#                 'name': col[0],
#                 'type': col[1],
#                 'choices': data_choices.get(col[1], ['Произвольное значение'])
#             }
#             for col in columns
#         ]
#         cursor.close()
#         connection.close()
#     except Exception as e:
#         error_message = f"Ошибка подключения: {str(e)}"
#     if request.method == 'POST':
#         num_records = int(request.POST.get('num_records', 10))
#         if user.pay_plan != True:
#             if user.limit_request < num_records:
#                 error_message = f"Превышен лимит запросов. Доступно: {user.limit_request}"
#                 return render(request, template_name='generate_fake_data.html', context={
#                     'project': project,
#                     'schema_name': schema_name,
#                     'table_name': table_name,
#                     'inserted_rows': inserted_rows,
#                     'record_count': record_count,
#                     'error_message': error_message
#                 })
#         try:
#             connection = psycopg2.connect(
#                 dbname=project.db_name,
#                 user=project.db_user,
#                 password=project.db_password,
#                 host=project.db_host,
#                 port=project.db_port
#             )
#             cursor = connection.cursor()
#             cursor.execute("""
#                 SELECT column_name, data_type
#                 FROM information_schema.columns
#                 WHERE table_schema = %s
#                   AND table_name = %s;
#             """, (schema_name, table_name))
#             columns = cursor.fetchall()
#             column_data = [{'name': col[0], 'type': col[1]} for col in columns]
#             column_names = [f'"{col["name"]}"' for col in column_data]  # Кавычки для SQL
#             placeholders = ', '.join(['%s' for _ in column_data])
#             insert_query = f'INSERT INTO "{schema_name}"."{table_name}" ({", ".join(column_names)}) VALUES ({placeholders})'
#             for _ in range(num_records):
#                 attempt = 0
#                 while attempt < retry_attempts:
#                     values = []
#                     for col in column_data:
#                         selected_value = request.POST.get(f'column_{col["name"]}', 'Произвольное значение')
#                         if selected_value == 'ФИО':
#                             values.append(fake.name())
#                         elif selected_value == 'Фамилия':
#                             values.append(fake.last_name())
#                         elif selected_value == 'Имя':
#                             values.append(fake.first_name())
#                         elif selected_value == 'Отчество':
#                             values.append(fake.middle_name())
#                         elif selected_value == 'Логин':
#                             values.append(fake.user_name())
#                         elif selected_value == 'Дата рождения':
#                             values.append(fake.date_of_birth(minimum_age=18, maximum_age=90))
#                         elif selected_value == 'Возраст':
#                             values.append(fake.random_int(min=18, max=90))
#                         elif selected_value == 'Пол':
#                             values.append(fake.random_element(['Мужской', 'Женский']))
#                         elif selected_value == 'Страна':
#                             values.append(fake.country())
#                         elif selected_value == 'Город':
#                             values.append(fake.city())
#                         elif selected_value == 'Адрес':
#                             values.append(fake.street_address())
#                         elif selected_value == 'Почтовый индекс':
#                             values.append(fake.postcode())
#                         elif selected_value == 'Email':
#                             values.append(fake.unique.email())
#                         elif selected_value == 'Телефон':
#                             values.append(fake.phone_number())
#                         elif selected_value == 'Широта':
#                             values.append(fake.latitude())
#                         elif selected_value == 'Долгота':
#                             values.append(fake.longitude())
#                         elif selected_value == 'Компания':
#                             values.append(fake.company())
#                         elif selected_value == 'Категория продукта':
#                             values.append(fake.word(ext_word_list=['Электроника', 'Книги', 'Одежда', 'Игрушки', 'Мебель', 'Транспорт']))
#                         elif selected_value == 'Должность':
#                             values.append(fake.job())
#                         elif selected_value == 'Отдел':
#                             values.append(fake.bs())
#                         elif selected_value == 'Валюта':
#                             values.append(fake.currency_name())
#                         elif selected_value == 'Символ валюты':
#                             values.append(fake.currency_symbol())
#                         elif selected_value == 'Кредитная карта':
#                             values.append(fake.credit_card_number())
#                         elif selected_value == 'IBAN':
#                             values.append(fake.iban())
#                         elif selected_value == 'Случайный текст (до 100 букв)':
#                             values.append(fake.text())
#                         elif selected_value == 'Заголовок':
#                             values.append(fake.catch_phrase())
#                         elif selected_value == 'Рейтинг (1-5)':
#                             values.append(fake.random_int(min=1, max=5))
#                         elif selected_value == 'Цена':
#                             values.append(fake.random_number(digits=5))
#                         elif selected_value == 'Цвет':
#                             values.append(fake.color_name())
#                         elif selected_value == 'Пароль':
#                             values.append(fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True))
#                         elif selected_value == 'IP-адрес':
#                             values.append(fake.ipv4())
#                         elif selected_value == 'Домен':
#                             values.append(fake.domain_name())
#                         elif selected_value == 'URL':
#                             values.append(fake.url())
#                         elif selected_value == 'URI':
#                             values.append(fake.uri())
#                         elif selected_value == 'UUID':
#                             values.append(fake.uuid4())
#                         elif selected_value == 'Число (большое)':
#                             values.append(fake.random_int(min=1, max=9000000))
#                         elif selected_value == 'Число (большое)':
#                             values.append(fake.random_int(min=1, max=900))
#                         elif selected_value == 'True/False':
#                             values.append(fake.boolean())
#                         elif selected_value == 'Случайный хэш':
#                             values.append(fake.sha256())
#                         elif selected_value == 'JSON-объект':
#                             values.append(fake.json())
#                         elif selected_value == 'Дата':
#                             values.append(fake.date())
#                         elif selected_value == 'Время':
#                             values.append(fake.time())
#                         elif selected_value == 'Дата и время':
#                             values.append(fake.date_time())
#                         elif selected_value == 'Временная зона':
#                             values.append(fake.timezone())
#                         elif selected_value == 'Дата в прошлом':
#                             values.append(fake.past_date())
#                         elif selected_value == 'Дата в будущем':
#                             values.append(fake.future_date())
#                         else:
#                             values.append(None)
#                     try:
#                         cursor.execute(insert_query, values)
#                         inserted_rows += 1
#                         break  # Успешная вставка, выходим из цикла
#                     except psycopg2.IntegrityError:
#                         connection.rollback()  # Откат транзакции в случае ошибки
#                         attempt += 1
#                         if attempt == retry_attempts:
#                             raise
#             connection.commit()
#             cursor.execute(f'SELECT COUNT(*) FROM "{schema_name}"."{table_name}";')
#             record_count = cursor.fetchone()[0]
#             cursor.close()
#             connection.close()
#             if user.pay_plan != True:
#                 user.limit_request = max(0, user.limit_request - num_records)
#                 user.save()
#         except psycopg2.IntegrityError as e:
#             error_message = f"Ошибка вставки данных (дубликат): {str(e)}"
#         except Exception as e:
#             error_message = f"Ошибка вставки данных: {str(e)}"
#     return render(request, template_name='generate_fake_data.html', context={
#         'info': info,
#         'project': project,
#         'schema_name': schema_name,
#         'table_name': table_name,
#         'column_data': column_data,
#         'inserted_rows': inserted_rows,
#         'record_count': record_count,
#         'error_message': error_message,
#     })


















# TODO
def generate_csv(request):
    """Создание файла CSV"""
    info = Info.objects.first()
    if request.method == 'POST':
        column_data = request.POST.getlist('fields')
        num_records = int(request.POST.get('num_records', 10))
        fake = Faker('ru_RU')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="fake_data.csv"'

        writer = csv.writer(response)
        writer.writerow(column_data)

        for _ in range(num_records):
            values = []
            for col in column_data:
                selected_value = col

                if selected_value == 'ФИО':
                    values.append(fake.name())
                elif selected_value == 'Фамилия':
                    values.append(fake.last_name())
                elif selected_value == 'Имя':
                    values.append(fake.first_name())
                elif selected_value == 'Отчество':
                    values.append(fake.middle_name())
                elif selected_value == 'Логин':
                    values.append(fake.user_name())
                elif selected_value == 'Дата рождения':
                    values.append(fake.date_of_birth(minimum_age=18, maximum_age=90))
                elif selected_value == 'Возраст':
                    values.append(fake.random_int(min=18, max=90))
                elif selected_value == 'Пол':
                    values.append(fake.random_element(['Мужской', 'Женский']))
                elif selected_value == 'Страна':
                    values.append(fake.country())
                elif selected_value == 'Город':
                    values.append(fake.city())
                elif selected_value == 'Адрес':
                    values.append(fake.street_address())
                elif selected_value == 'Почтовый индекс':
                    values.append(fake.postcode())
                elif selected_value == 'Email':
                    values.append(fake.unique.email())
                elif selected_value == 'Телефон':
                    values.append(fake.phone_number())
                elif selected_value == 'Широта':
                    values.append(fake.latitude())
                elif selected_value == 'Долгота':
                    values.append(fake.longitude())
                elif selected_value == 'Компания':
                    values.append(fake.company())
                elif selected_value == 'Категория продукта':
                    values.append(fake.word(ext_word_list=['Электроника', 'Книги', 'Одежда', 'Игрушки', 'Мебель', 'Транспорт']))
                elif selected_value == 'Должность':
                    values.append(fake.job())
                elif selected_value == 'Отдел':
                    values.append(fake.bs())
                elif selected_value == 'Валюта':
                    values.append(fake.currency_name())
                elif selected_value == 'Символ валюты':
                    values.append(fake.currency_symbol())
                elif selected_value == 'Кредитная карта':
                    values.append(fake.credit_card_number())
                elif selected_value == 'IBAN':
                    values.append(fake.iban())
                elif selected_value == 'Случайный текст (до 100 букв)':
                    values.append(fake.text())
                elif selected_value == 'Заголовок':
                    values.append(fake.catch_phrase())
                elif selected_value == 'Рейтинг (1-5)':
                    values.append(fake.random_int(min=1, max=5))
                elif selected_value == 'Цена':
                    values.append(fake.random_number(digits=5))
                elif selected_value == 'Цвет':
                    values.append(fake.color_name())
                elif selected_value == 'Пароль':
                    values.append(fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True))
                elif selected_value == 'IP-адрес':
                    values.append(fake.ipv4())
                elif selected_value == 'Домен':
                    values.append(fake.domain_name())
                elif selected_value == 'URL':
                    values.append(fake.url())
                elif selected_value == 'URI':
                    values.append(fake.uri())
                elif selected_value == 'UUID':
                    values.append(fake.uuid4())
                elif selected_value == 'Число (большое)':
                    values.append(fake.random_int(min=1, max=9000000))
                elif selected_value == 'Число (маленькое)':
                    values.append(fake.random_int(min=1, max=900))
                elif selected_value == 'True/False':
                    values.append(fake.boolean())
                elif selected_value == 'Случайный хэш':
                    values.append(fake.sha256())
                elif selected_value == 'JSON-объект':
                    values.append(fake.json())
                elif selected_value == 'Дата':
                    values.append(fake.date())
                elif selected_value == 'Время':
                    values.append(fake.time())
                elif selected_value == 'Дата и время':
                    values.append(fake.date_time())
                elif selected_value == 'Временная зона':
                    values.append(fake.timezone())
                elif selected_value == 'Дата в прошлом':
                    values.append(fake.past_date())
                elif selected_value == 'Дата в будущем':
                    values.append(fake.future_date())
                else:
                    values.append(None)

            writer.writerow(values)

        return response

    return render(request, template_name='generate_csv.html', context={
        'info': info,
        'choices_list': choices_list["text"]
    })


# TODO
def random_joke(request):
    """Генерация случайной шутки с выбором тематики"""
    info = Info.objects.first()
    selected_category = 'all'
    if request.method == 'POST':
        selected_category = request.POST.get('category', 'neutral')
    try:
        jokes = pyjokes.get_joke(language="ru", category=selected_category)
    except Exception as e:
        jokes = f"Ошибка при получении шутки: {str(e)}"
    return render(request, template_name='random_joke.html', context={
        'info': info,
        'jokes': jokes,
        'selected_category': selected_category
    })
