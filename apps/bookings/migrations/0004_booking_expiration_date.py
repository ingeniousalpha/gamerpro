# Generated by Django 4.1.7 on 2023-06-24 08:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0003_depositreplenishment'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='expiration_date',
            field=models.DateTimeField(auto_now=True),
        ),
    ]