from . import views
from django.urls import path
from work_db.views import home, about_us, profile, database_detail, database_edit, database_delete
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', home, name='home'),
    path('about_us/', about_us, name='about_us'),
    path('profile/', profile, name='profile'),

    path('database/<int:pk>/', database_detail, name='database_detail'),
    path('database/<int:pk>/edit/', database_edit, name='database_edit'),
    path('database/<int:pk>/delete/', database_delete, name='database_delete'),

    # path('login/', auth_views.LoginView.as_view(), name='login'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    # path('register/', your_register_view, name='register'),


    # path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    # path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    # path('register/', views.register, name='register'),
    # path('profile/', views.profile, name='profile'),
]
