from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import login
from .forms import CustomUserCreationForm, DataBaseUserForm
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth import logout
from .models import Info, DataBaseUser


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


# TODO
@login_required
def profile(request):
    """Страница профиля пользователя"""
    user_databases = DataBaseUser.objects.filter(user=request.user)
    return render(request, template_name='profile.html', context={
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
    return render(request, 'registration/register.html', {'form': form})


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
        'database': database})


@login_required
def database_edit(request, pk):
    """Редактирование информации о базе данных"""
    database = get_object_or_404(DataBaseUser, pk=pk)
    if request.method == 'POST':
        form = DataBaseUserForm(request.POST, instance=database)
        if form.is_valid():
            form.save()
            return redirect('database_detail', pk=pk)
        else:
            form.add_error(None, "Пожалуйста, исправьте ошибки в форме")
    else:
        form = DataBaseUserForm(instance=database)
        form.fields['db_password'].widget.attrs['value'] = database.db_password
    return render(request, template_name='database_edit.html', context={
        'form': form,
        'database': database})


@login_required
def database_delete(request, pk):
    """Удаление проекта базы данных"""
    database = get_object_or_404(DataBaseUser, pk=pk)
    database.delete()
    messages.success(request, 'Проект успешно удален.')
    return redirect('profile')
