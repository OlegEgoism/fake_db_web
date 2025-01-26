from django.urls import path
from django.contrib.auth import views as auth_views
from work_db.views import (
    home,
    about_us,

    profile,
    register,
    logout_view,

    database_detail,
    database_edit,
    database_delete
)

urlpatterns = [
    path('', home, name='home'),
    path('about_us/', about_us, name='about_us'),

    path('profile/', profile, name='profile'),
    path('register/', register, name='register'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),

    path('database/<int:pk>/', database_detail, name='database_detail'),
    path('database/<int:pk>/edit/', database_edit, name='database_edit'),
    path('database/<int:pk>/delete/', database_delete, name='database_delete'),
]
