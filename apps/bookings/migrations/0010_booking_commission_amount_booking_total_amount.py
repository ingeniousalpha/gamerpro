# Generated by Django 4.1.7 on 2023-08-17 04:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0009_alter_booking_use_balance'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='commission_amount',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=8),
        ),
        migrations.AddField(
            model_name='booking',
            name='total_amount',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=8),
        ),
    ]
