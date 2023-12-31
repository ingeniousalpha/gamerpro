# Generated by Django 4.1.7 on 2023-09-30 09:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clubs', '0022_clubtimepacket_priority'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='clubtimepacket',
            options={'verbose_name': 'Пакет', 'verbose_name_plural': 'Пакеты'},
        ),
        migrations.AlterModelOptions(
            name='clubtimepacketgroup',
            options={'verbose_name': 'Группа Пакетов', 'verbose_name_plural': 'Группы Пакетов'},
        ),
        migrations.AddField(
            model_name='clubtimepacket',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
