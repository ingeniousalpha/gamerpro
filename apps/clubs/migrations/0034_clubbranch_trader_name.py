# Generated by Django 4.1.7 on 2024-02-01 17:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clubs', '0033_alter_club_options_club_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='clubbranch',
            name='trader_name',
            field=models.CharField(default='', max_length=256),
        ),
    ]