# Generated by Django 4.1.7 on 2024-09-22 13:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0021_booking_use_cashback'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='is_time_packet_set',
            field=models.BooleanField(default=False),
        ),
    ]