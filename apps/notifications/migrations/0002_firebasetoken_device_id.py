# Generated by Django 4.1.7 on 2023-09-10 12:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='firebasetoken',
            name='device_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
