# Generated by Django 4.1.7 on 2024-07-06 11:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0020_alter_booking_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='use_cashback',
            field=models.BooleanField(default=False),
        ),
    ]
