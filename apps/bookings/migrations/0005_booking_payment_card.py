# Generated by Django 4.1.7 on 2023-06-25 11:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0004_alter_paymentcard_pay_token'),
        ('bookings', '0004_booking_expiration_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='payment_card',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bookings', to='payments.paymentcard'),
        ),
    ]