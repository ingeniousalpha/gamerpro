# Generated by Django 4.1.7 on 2023-08-06 12:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0008_alter_booking_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='use_balance',
            field=models.BooleanField(default=False),
        ),
    ]