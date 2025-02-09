# 🛠 Fake Tools Suite  


## 🚀 Развитие проекта – Ищем участников!  
Этот проект создается **для развития** и мы ищем **разработчиков, энтузиастов и единомышленников**, которые хотят участвовать в создании полезного инструмента для тестирования и анализа данных.  
🔹 Если вам **интересна работа с данными**, **OCR**, **разработка API**, **интерфейсов** или **алгоритмов генерации данных**, присоединяйтесь к проекту!  
📩 **Свяжитесь со мной** или создайте Pull Request, если хотите внести вклад!  


## 📥 Установка  
Создайте файл ".env" и укажите необходимые настройки -
# Подключение к базе данных
POSTGRES_DB=name_db
POSTGRES_USER=user_db
POSTGRES_PASSWORD=pass_db
DB_HOST=localhost
DB_PORT=5432
# Отправка уведомлений на электронную почту
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=...........mail.com
EMAIL_HOST_PASSWORD=..................
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# Авторизация через соц.сеть google
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=.............................
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=..........................


## 📥 Админка
Заполните в админке новые записи для - "Информация на сайте" и "Настройки проекта".
Заполните "Список баз данных" и укажите базы данных для работы - 
'Hive'
'Greenplum'
'MySQL' 
'Oracle' 
'PostgreSQL' 

[fake.webm](..%2F..%2F..%2F%D0%92%D0%B8%D0%B4%D0%B5%D0%BE%2F%D0%97%D0%B0%D0%BF%D0%B8%D1%81%D0%B8%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%2Ffake.webm)

```bash
git clone https://github.com/your-username/fake-tools-suite.git
cd fake-tools-suite
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver





