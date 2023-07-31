# Generated by Django 4.1.5 on 2023-07-04 08:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_alter_console_options_alter_models_type_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scooter',
            name='accumulator',
        ),
        migrations.RemoveField(
            model_name='scooter',
            name='chargetime',
        ),
        migrations.RemoveField(
            model_name='scooter',
            name='maxload',
        ),
        migrations.RemoveField(
            model_name='scooter',
            name='maxspeed',
        ),
        migrations.RemoveField(
            model_name='scooter',
            name='power',
        ),
        migrations.RemoveField(
            model_name='scooter',
            name='weight',
        ),
        migrations.AlterField(
            model_name='cooking',
            name='type',
            field=models.CharField(choices=[('Электрогриль', 'Электрогриль'), ('Соковыжималка', 'Соковыжималка'), ('Сушилка', 'Сушилка')], max_length=25, verbose_name='Вид устройства'),
        ),
        migrations.AlterField(
            model_name='models',
            name='type',
            field=models.CharField(choices=[('Модемы', 'Модемы'), ('Роутеры', 'Роутеры'), ('Zala', 'Zala'), ('Умный Дом', 'Умный Дом'), ('Смартфоны', 'Смартфоны'), ('Телевизоры', 'Телевизоры'), ('Игровые приставки', 'Игровые приставки'), ('Ноутбуки', 'Ноутбуки'), ('Планшеты', 'Планшеты'), ('Умные часы', 'Умные часы'), ('Электросамокаты', 'Электросамокаты'), ('Электровелосипеды', 'Электровелосипеды'), ('Пылесосы', 'Пылесосы'), ('Роботы-пылесосы', 'Роботы пылесосы'), ('Мойщики окон', 'Мойщики окон'), ('Кофемашины', 'Кофемашины'), ('Кофеварки', 'Кофеварки'), ('Электрогрили', 'Электрогрили'), ('Соковыжималки', 'Соковыжималки'), ('Сушилки', 'Сушилки'), ('Кондиционеры', 'Кондиционеры'), ('Умные колонки', 'Умные колонки'), ('Аудиосистемы', 'Аудиосистемы'), ('Прочее оборудование', 'Прочее оборудование')], max_length=50, verbose_name='Вид оборудования'),
        ),
    ]
