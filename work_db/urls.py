from django.urls import path
from django.contrib.auth import views as auth_views
from work_db.views import (
    home,
    about_us,

    profile,
    edit_profile,

    register,
    logout_view,
    request_account_deletion,
    confirm_account_deletion,
    verify_email,

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

    random_joke,

)

urlpatterns = [
    path('', home, name='home'),
    path('about_us/', about_us, name='about_us'),

    path('profile/', profile, name='profile'),
    path('profile/edit/', edit_profile, name='edit_profile'),
    path("delete-account/", request_account_deletion, name="request_account_deletion"),
    path("confirm-delete/", confirm_account_deletion, name="confirm_account_deletion"),

    path('register/', register, name='register'),
    path("verify-email/<uidb64>/<token>/", verify_email, name="verify_email"),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html',
                                                                 email_template_name='registration/password_reset_email.html',
                                                                 html_email_template_name='registration/password_reset_email.html',
                                                                 subject_template_name='registration/password_reset_subject.txt',
                                                                 success_url='/password-reset/done/'
                                                                 ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html', success_url='/password-reset/complete/'), name='password_reset_confirm'),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),

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
