# Generated by Django 4.1.7 on 2023-06-23 17:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_outer_payer_id_user_secret_key'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='secret_key',
            field=models.UUIDField(unique=True, verbose_name='Секретный ключ'),
        ),
    ]
