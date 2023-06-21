# Generated by Django 4.1.5 on 2023-06-17 08:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Console',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('memory', models.PositiveSmallIntegerField(verbose_name='Объём накопителя')),
                ('image', models.ImageField(blank=True, null=True, upload_to='main/media')),
                ('actual', models.CharField(choices=[('Да', 'Да'), ('Нет', 'Нет')], default='Да', max_length=3, verbose_name='Актуально')),
                ('model', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.models', verbose_name='Модель оборудования')),
                ('purpose', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.purpose', verbose_name='Назначение')),
            ],
            options={
                'verbose_name': 'Игровая приставка',
                'verbose_name_plural': 'Игровые приставки',
            },
        ),
    ]