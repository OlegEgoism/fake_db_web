from django.urls import path
from django.contrib.auth import views as auth_views
from work_db.views import (
    home,
    about_us,

    profile,
    edit_profile,
    register,
    logout_view,

    database_detail,
    database_edit,
    database_delete,

    create_project,
    my_projects,
    connect_to_database,
    database_schemas,
    schema_tables,
    table_columns,
    generate_fake_data,

    random_joke
)

urlpatterns = [
    path('', home, name='home'),
    path('about_us/', about_us, name='about_us'),

    path('profile/', profile, name='profile'),
    path('profile/edit/', edit_profile, name='edit_profile'),

    path('register/', register, name='register'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),

    path('database/<int:pk>/', database_detail, name='database_detail'),
    path('database/<int:pk>/edit/', database_edit, name='database_edit'),
    path('database/<int:pk>/delete/', database_delete, name='database_delete'),

    path('create-project/', create_project, name='create_project'),
    path('my_projects/', my_projects, name='my_projects'),
    path('connect/<int:pk>/', connect_to_database, name='connect_to_database'),
    path('schemas/<int:pk>/', database_schemas, name='database_schemas'),
    path('schemas/<int:pk>/<str:schema_name>/', schema_tables, name='schema_tables'),
    path('schemas/<int:pk>/<str:schema_name>/<str:table_name>/', table_columns, name='table_columns'),
    path('schemas/<int:pk>/<str:schema_name>/<str:table_name>/generate/', generate_fake_data, name='generate_fake_data'),

    path('random_joke/', random_joke, name='random_joke'),
]