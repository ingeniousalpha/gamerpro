# Generated by Django 4.1.7 on 2024-02-16 16:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clubs', '0036_clubcomputer_is_broken'),
    ]

    operations = [
        migrations.AddField(
            model_name='clubbranch',
            name='is_ready',
            field=models.BooleanField(default=False),
        ),
    ]
