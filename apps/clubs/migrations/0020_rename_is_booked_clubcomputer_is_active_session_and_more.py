# Generated by Django 4.1.7 on 2023-09-17 05:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clubs', '0019_clubbranch_image'),
    ]

    operations = [
        migrations.RenameField(
            model_name='clubcomputer',
            old_name='is_booked',
            new_name='is_active_session',
        ),
        migrations.AddField(
            model_name='clubcomputer',
            name='is_locked',
            field=models.BooleanField(default=False),
        ),
    ]