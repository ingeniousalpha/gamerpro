# Generated by Django 4.1.7 on 2024-08-12 17:20

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('clubs', '0047_clubperk'),
    ]

    operations = [
        migrations.AddField(
            model_name='clubbranchuser',
            name='created_at',
            field=models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name='Время создания'),
        ),
        migrations.AddField(
            model_name='clubbranchuser',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True, verbose_name='Время последнего изменения'),
        ),
    ]