# Generated by Django 4.1.7 on 2023-05-03 15:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clubs', '0015_alter_clubbranchhardware_group_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='clubbranch',
            old_name='ip_address',
            new_name='api_host',
        ),
        migrations.AddField(
            model_name='clubbranch',
            name='api_password',
            field=models.CharField(max_length=20, null=True, verbose_name='Пароль для API филиала'),
        ),
        migrations.AddField(
            model_name='clubbranch',
            name='api_user',
            field=models.CharField(max_length=20, null=True, verbose_name='Логин для API филиала'),
        ),
    ]