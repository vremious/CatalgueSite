Сайт-приложение для контроля за остатками оборудования в нескольких сервисных центрах.

Возможности сайта:
1) Создание каталога оборудования по категориям (аналог интрнет-магазина) с добавлением категорий, назначений, производителей и моделей оборудования пользователями
2) Контроль за количеством единиц оборудования в сервисных центрах пользователями
3) Гибкая функциональность админ-панели 


Для корректного функционирования сайта нужен .env файл вида:

DB_ENGINE =  django.db.backends.postgresql_psycopg2

DB_NAME = your_db_name

DB_PASSWORD = your_db_password

DB_USER  = your_db_user

DB_HOST  = your_db_host

DB_PORT  = your_db_port

DEBUG = True

SECRET_KEY = 'your_secret_key'

