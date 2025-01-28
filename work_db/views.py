import os
import psycopg2
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import login
from faker import Faker
from .data.data_choices_list import choices_list
from .forms import CustomUserCreationForm, DataBaseUserForm
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth import logout
from .models import Info, DataBaseUser
import pyjokes

connect_timeout = int(os.getenv('CONNECT_TIMEOUT'))
limit_create_db = int(os.getenv('LIMIT_CREATE_DB'))


def home(request):
    """Главная"""
    info = Info.objects.first()
    return render(request, template_name='home.html', context={
        'info': info})


def about_us(request):
    """Страница о нас"""
    info = Info.objects.first()
    return render(request, template_name='about_us.html', context={
        'info': info})


@login_required
def profile(request):
    """Страница профиля пользователя"""
    info = Info.objects.first()
    user_databases = DataBaseUser.objects.filter(user=request.user)
    return render(request, template_name='profile.html', context={
        'info': info,
        'user': request.user,
        'user_databases': user_databases})


def register(request):
    """Регистрация пользователя"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, template_name='registration/register.html', context={
        'form': form})


def logout_view(request):
    """Выход пользователя"""
    logout(request)
    return redirect('home')


@login_required
def database_detail(request, pk):
    """Страница информации о конкретной базе данных пользователя"""
    database = get_object_or_404(DataBaseUser, pk=pk)
    return render(request, template_name='database_detail.html', context={
        'database': database})


@login_required
def database_edit(request, pk):
    """Редактирование информации о базе данных и проверка подключения"""
    info = Info.objects.first()
    database = get_object_or_404(DataBaseUser, pk=pk)
    form = DataBaseUserForm(instance=database)
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
    return render(request, 'database_edit.html', {
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
    for i in projects:
        print(i.data_base_name)
    return render(request, template_name='my_projects.html', context={
        'info': info,
        'projects': projects})


def connect_to_database(request, pk):
    """Получаем объект базы данных"""
    info = Info.objects.first()
    project = get_object_or_404(DataBaseUser, pk=pk)
    connection_status = None
    error_message = None
    try:
        connection = psycopg2.connect(
            dbname=project.db_name,
            user=project.db_user,
            password=project.db_password,
            host=project.db_host,
            port=project.db_port,
            connect_timeout=connect_timeout
        )
        connection_status = f"Успешное подключение к базе данных '{project.db_name}'"
        connection.close()
    except Exception as e:
        error_message = f"Ошибка подключения: {str(e)}"
    return render(request, template_name='connect_result.html', context={
        'info': info,
        'project': project,
        'connection_status': connection_status,
        'error_message': error_message
    })


def database_schemas(request, pk):
    """Получаем список схем в базе данных"""
    project = get_object_or_404(DataBaseUser, pk=pk)
    schemas = []
    error_message = None
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
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_toast', 'pg_catalog', 'information_schema')
            ORDER BY schema_name;
        """)
        schemas = [row[0] for row in cursor.fetchall()]
        cursor.close()
        connection.close()
    except Exception as e:
        error_message = f"Ошибка подключения: {str(e)}"
    return render(request, template_name='database_schemas.html', context={
        'project': project,
        'schemas': schemas,
        'error_message': error_message
    })


def schema_tables(request, pk, schema_name):
    """Получения информации о схеме"""
    project = get_object_or_404(DataBaseUser, pk=pk)
    tables = []
    error_message = None
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
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = %s;
        """, (schema_name,))
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        connection.close()
    except Exception as e:
        error_message = f"Ошибка подключения: {str(e)}"
    return render(request, template_name='schema_tables.html', context={
        'project': project,
        'schema_name': schema_name,
        'tables': tables,
        'error_message': error_message
    })


def table_columns(request, pk, schema_name, table_name):
    """Получение информации о таблице и количестве записей"""
    project = get_object_or_404(DataBaseUser, pk=pk)
    columns = []
    record_count = 0
    error_message = None

    try:
        connection = psycopg2.connect(
            dbname=project.db_name,
            user=project.db_user,
            password=project.db_password,
            host=project.db_host,
            port=project.db_port
        )
        cursor = connection.cursor()

        # Получение колонок таблицы
        cursor.execute("""
            SELECT 
                column_name, 
                data_type, 
                COALESCE(
                    (SELECT pg_catalog.col_description(c.oid, cols.ordinal_position::int))
                    , 'Нет описания') AS column_comment
            FROM information_schema.columns cols
            JOIN pg_catalog.pg_class c 
                ON c.relname = cols.table_name
            WHERE cols.table_schema = %s 
              AND cols.table_name = %s;
        """, (schema_name, table_name))
        columns = cursor.fetchall()

        # Получение количества записей в таблице
        cursor.execute(f'SELECT COUNT(*) FROM "{schema_name}"."{table_name}";')
        record_count = cursor.fetchone()[0]

        cursor.close()
        connection.close()
    except Exception as e:
        error_message = f"Ошибка подключения: {str(e)}"

    return render(request, template_name='table_columns.html', context={
        'project': project,
        'schema_name': schema_name,
        'table_name': table_name,
        'columns': columns,
        'record_count': record_count,
        'error_message': error_message
    })


def generate_fake_data(request, pk, schema_name, table_name):
    """Генерация случайных данных для указанной таблицы"""
    project = get_object_or_404(DataBaseUser, pk=pk)
    fake = Faker('ru_RU')
    error_message = None
    inserted_rows = 0
    record_count = 0  # Переменная для хранения количества записей
    retry_attempts = 200  # Количество попыток вставки при ошибке
    data_choices = choices_list

    try:
        connection = psycopg2.connect(
            dbname=project.db_name,
            user=project.db_user,
            password=project.db_password,
            host=project.db_host,
            port=project.db_port
        )
        cursor = connection.cursor()

        # Получение количества записей в таблице
        cursor.execute(f'SELECT COUNT(*) FROM "{schema_name}"."{table_name}";')
        record_count = cursor.fetchone()[0]

        # Получение информации о колонках
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
        try:
            num_records = int(request.POST.get('num_records', 10))
            connection = psycopg2.connect(
                dbname=project.db_name,
                user=project.db_user,
                password=project.db_password,
                host=project.db_host,
                port=project.db_port
            )
            cursor = connection.cursor()

            column_names = [f'"{col["name"]}"' for col in column_data]  # Кавычки для имен колонок
            placeholders = ', '.join(['%s' for _ in column_data])
            insert_query = f'INSERT INTO "{schema_name}"."{table_name}" ({", ".join(column_names)}) VALUES ({placeholders})'

            for _ in range(num_records):
                attempt = 0
                while attempt < retry_attempts:
                    values = []
                    for col in column_data:
                        selected_value = request.POST.get(f'column_{col["name"]}', 'Произвольное значение')
                        if selected_value == 'Имя':
                            values.append(fake.first_name())
                        elif selected_value == 'Фамилия':
                            values.append(fake.last_name())
                        elif selected_value == 'Email':
                            values.append(fake.unique.email())
                        elif selected_value == 'Телефон':
                            values.append(fake.phone_number())
                        elif selected_value == 'URL':
                            values.append(fake.url())
                        elif selected_value == 'Дата рождения':
                            values.append(fake.date_of_birth(minimum_age=18, maximum_age=90))
                        elif selected_value == 'Кредитная карта':
                            values.append(fake.credit_card_number())
                        elif selected_value == 'Рейтинг (1-5)':
                            values.append(fake.random_int(min=1, max=5))
                        elif selected_value == 'UUID':
                            values.append(fake.uuid4())
                        elif selected_value == 'IP-адрес (v4)':
                            values.append(fake.ipv4())
                        elif selected_value == 'True/False':
                            values.append(fake.boolean())
                        elif selected_value == 'Цена':
                            values.append(fake.random_number(digits=5))
                        else:
                            values.append(None)
                    try:
                        cursor.execute(insert_query, values)
                        inserted_rows += 1
                        break  # Успешная вставка, выходим из цикла
                    except psycopg2.IntegrityError:
                        connection.rollback()  # Откат транзакции в случае ошибки
                        attempt += 1
                        if attempt == retry_attempts:
                            raise
            connection.commit()

            # Обновление количества записей после вставки
            cursor.execute(f'SELECT COUNT(*) FROM "{schema_name}"."{table_name}";')
            record_count = cursor.fetchone()[0]

            cursor.close()
            connection.close()
        except psycopg2.IntegrityError as e:
            error_message = f"Ошибка вставки данных (дубликат): {str(e)}"
        except Exception as e:
            error_message = f"Ошибка вставки данных: {str(e)}"

    return render(request, 'generate_fake_data.html', {
        'project': project,
        'schema_name': schema_name,
        'table_name': table_name,
        'column_data': column_data,
        'inserted_rows': inserted_rows,
        'record_count': record_count,
        'error_message': error_message
    })


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
        'jokes': jokes,
        'info': info,
        'selected_category': selected_category
    })
