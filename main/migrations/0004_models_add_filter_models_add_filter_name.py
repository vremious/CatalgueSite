# Generated by Django 4.1.5 on 2023-09-25 10:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_addfilter1'),
    ]

    operations = [
        migrations.AddField(
            model_name='models',
            name='add_filter',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='main.addfilter1', verbose_name='Значение фильтра'),
        ),
        migrations.AddField(
            model_name='models',
            name='add_filter_name',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='main.addfiltername1', verbose_name='Название дополнительного фильтра'),
        ),
    ]
