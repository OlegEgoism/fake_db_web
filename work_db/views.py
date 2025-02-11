import csv
import random
import psycopg2
from PIL import Image
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail, EmailMessage
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import login
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from faker import Faker
from .data.data_choices_list import choices_list, generate_fake_value
from .data.db_connection import get_db_connection
from .forms import CustomUserCreationForm, DataBaseUserForm, CustomUserForm, ImageUploadForm
from django.contrib import messages
from django.contrib.auth import logout
from .models import Info, DataBaseUser, AppSettings, DeletionConfirmation
from django.contrib.auth import get_user_model
import pyjokes
import re
from django.contrib.auth.decorators import login_required
from psycopg2 import sql
import pytesseract

User = get_user_model()
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'


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


# TODO Пользователь
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


# TODO База данных
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
    """Мои проекты базы данных с поиском"""
    info = Info.objects.first()
    search_query = request.GET.get("search", "").strip()
    projects = DataBaseUser.objects.filter(user=request.user)
    if search_query:
        projects = projects.filter(Q(db_project__icontains=search_query))
    projects = projects.order_by("db_date_create")
    return render(request, template_name="my_projects.html", context={
        "info": info,
        "projects": projects,
        "search_query": search_query
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
def create_schema(request, pk):
    """Создаёт новую схему в базе данных"""
    project = get_object_or_404(DataBaseUser, pk=pk)
    error_message = None

    if request.method == "POST":
        schema_name = request.POST.get("schema_name").strip()

        # Проверка имени схемы (только буквы, цифры и _)
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", schema_name):
            messages.error(request, "Название схемы может содержать только буквы, цифры и '_', но не начинаться с цифры.")
            return redirect("create_schema", pk=pk)

        connection, error_message = get_db_connection(project)
        if connection:
            try:
                with connection.cursor() as cursor:
                    # Проверяем, существует ли схема
                    check_schema_query = sql.SQL("""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.schemata 
                            WHERE schema_name = %s
                        );
                    """)
                    cursor.execute(check_schema_query, (schema_name,))
                    schema_exists = cursor.fetchone()[0]

                    if schema_exists:
                        messages.error(request, f"Схема '{schema_name}' уже существует!")
                        return redirect("create_schema", pk=pk)

                    # Создаём схему
                    create_schema_query = sql.SQL("CREATE SCHEMA {};").format(
                        sql.Identifier(schema_name)
                    )
                    cursor.execute(create_schema_query)
                    connection.commit()

                messages.success(request, f"Схема '{schema_name}' успешно создана!")
                return redirect("database_schemas", pk=pk)
            except Exception as e:
                error_message = f"Ошибка создания схемы: {str(e)}"
            finally:
                connection.close()

    return render(request, "create_schema.html", {"project": project, "error_message": error_message})


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
        try:
            with connection.cursor() as cursor:
                # Проверяем, существует ли таблица
                check_table_query = sql.SQL("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = %s AND table_name = %s
                    );
                """)
                cursor.execute(check_table_query, (schema_name, table_name))
                table_exists = cursor.fetchone()[0]

                if not table_exists:
                    error_message = f"Ошибка: Таблица '{table_name}' в схеме '{schema_name}' не существует!"
                    return render(request, "table_columns.html", {
                        "info": info,
                        "project": project,
                        "schema_name": schema_name,
                        "table_name": table_name,
                        "columns": [],
                        "record_count": 0,
                        "error_message": error_message
                    })

                # Получаем список колонок таблицы
                query = sql.SQL("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = %s 
                      AND table_name = %s;
                """)
                cursor.execute(query, (schema_name, table_name))
                columns = cursor.fetchall()

                # Получаем количество записей
                count_query = sql.SQL('SELECT COUNT(*) FROM {}.{};').format(
                    sql.Identifier(schema_name),
                    sql.Identifier(table_name)
                )
                cursor.execute(count_query)
                record_count = cursor.fetchone()[0]

        except Exception as e:
            error_message = f"Ошибка: {str(e)}"
        finally:
            connection.close()

    return render(request, "table_columns.html", {
        "info": info,
        "project": project,
        "schema_name": schema_name,
        "table_name": table_name,
        "columns": columns,
        "record_count": record_count,
        "error_message": error_message
    })


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


@login_required
def view_table_data(request, pk, schema_name, table_name):
    """Просмотр данных из таблицы с пагинацией"""
    info = Info.objects.first()
    project = get_object_or_404(DataBaseUser, pk=pk)
    connection, error_message = get_db_connection(project)
    view_table_db = AppSettings.objects.first()
    if error_message:
        return render(request, template_name='error_page.html', context={'error_message': error_message})
    cursor = connection.cursor()
    cursor.execute(f"""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s;
    """, (schema_name, table_name))
    columns = [col[0] for col in cursor.fetchall()]
    cursor.execute(f'SELECT COUNT(*) FROM "{schema_name}"."{table_name}";')
    record_count = cursor.fetchone()[0]
    cursor.execute(f'SELECT * FROM "{schema_name}"."{table_name}";')
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    page_size = view_table_db.view_table_db if view_table_db else 50
    paginator = Paginator(rows, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    records_on_page = len(page_obj.object_list)
    return render(request, template_name='view_table_data.html', context={
        'info': info,
        'project': project,
        'schema_name': schema_name,
        'table_name': table_name,
        'columns': columns,
        'page_obj': page_obj,
        'record_count': record_count,
        'records_on_page': records_on_page
    })


@login_required
def create_table(request, pk, schema_name):
    """Создание таблицы в указанной схеме базы данных"""
    info = Info.objects.first()
    project = get_object_or_404(DataBaseUser, pk=pk)
    error_message = None
    if request.method == "POST":
        table_name = request.POST.get("table_name")
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table_name):
            messages.error(request, "Название таблицы может содержать только буквы, цифры и '_', но не начинаться с цифры.")
            return render(request, "create_table.html", {"project": project, "schema_name": schema_name})
        column_names = request.POST.getlist("column_name[]")
        column_types = request.POST.getlist("column_type[]")
        if not table_name or not column_names:
            messages.error(request, "Введите название таблицы и хотя бы один столбец.")
            return render(request, "create_table.html", {"project": project, "schema_name": schema_name})
        connection, error_message = get_db_connection(project)
        if connection:
            try:
                with connection.cursor() as cursor:
                    check_table_query = sql.SQL("""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.tables 
                            WHERE table_schema = %s AND table_name = %s
                        );
                    """)
                    cursor.execute(check_table_query, (schema_name, table_name))
                    table_exists = cursor.fetchone()[0]
                    if table_exists:
                        messages.error(request, f"Таблица '{table_name}' уже существует в схеме '{schema_name}'.")
                        return render(request, "create_table.html", {"project": project, "schema_name": schema_name})
                    columns_sql = ", ".join([f'"{name}" {type}' for name, type in zip(column_names, column_types)])
                    create_table_sql = sql.SQL(
                        'CREATE TABLE {}.{} (id SERIAL PRIMARY KEY, {});'
                    ).format(
                        sql.Identifier(schema_name),
                        sql.Identifier(table_name),
                        sql.SQL(columns_sql)
                    )
                    cursor.execute(create_table_sql)
                    connection.commit()
                messages.success(request, f"Таблица '{table_name}' успешно создана в схеме '{schema_name}'.")
                return redirect("schema_tables", pk=pk, schema_name=schema_name)
            except Exception as e:
                error_message = f"Ошибка создания таблицы: {str(e)}"
            finally:
                connection.close()
    return render(request, template_name="create_table.html", context={
        'info': info,
        "project": project,
        "schema_name": schema_name,
        "error_message": error_message
    })


@login_required
def delete_table(request, pk, schema_name, table_name):
    """Удаляет указанную таблицу из схемы"""
    project = get_object_or_404(DataBaseUser, pk=pk)
    connection, error_message = get_db_connection(project)
    if connection:
        try:
            with connection.cursor() as cursor:
                # Проверяем, существует ли таблица перед удалением
                check_table_query = sql.SQL("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = %s AND table_name = %s
                    );
                """)
                cursor.execute(check_table_query, (schema_name, table_name))
                table_exists = cursor.fetchone()[0]
                if not table_exists:
                    messages.error(request, f"Таблица '{table_name}' в схеме '{schema_name}' не существует!")
                    return redirect("schema_tables", pk=pk, schema_name=schema_name)
                delete_query = sql.SQL('DROP TABLE {}.{} CASCADE;').format(
                    sql.Identifier(schema_name),
                    sql.Identifier(table_name)
                )
                cursor.execute(delete_query)
                connection.commit()
                messages.success(request, f"Таблица '{table_name}' успешно удалена!")
        except Exception as e:
            messages.error(request, f"Ошибка при удалении таблицы: {str(e)}")
        finally:
            connection.close()
    return redirect("schema_tables", pk=pk, schema_name=schema_name)


# TODO Создание CSV
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
            values = [generate_fake_value(col, col, fake) for col in column_data]
            writer.writerow(values)
        return response
    return render(request, template_name='generate_csv.html', context={
        'info': info,
        'choices_list': choices_list["text"]
    })


# TODO Шутки
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


# TODO Распознавание
def recognize_text(request):
    """Распознавание текста"""
    recognized_text = None
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_image = form.save()
            image_path = uploaded_image.image.path
            img = Image.open(image_path)
            recognized_text = pytesseract.image_to_string(img, lang='rus+eng')
            request.session['recognized_text'] = recognized_text  # Сохраняем текст в сессии
    else:
        form = ImageUploadForm()
    return render(request, template_name='recognize_text.html', context={
        'form': form,
        'recognized_text': recognized_text
    })


def download_text(request):
    """Скачивание распознанного текста"""
    recognized_text = request.session.get('recognized_text', '')  # Получаем текст из сессии
    response = HttpResponse(recognized_text, content_type="text/plain; charset=utf-8")
    response['Content-Disposition'] = 'attachment; filename="recognized_text.txt"'
    return response
