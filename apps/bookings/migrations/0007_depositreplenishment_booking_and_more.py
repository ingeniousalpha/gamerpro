# Generated by Django 4.1.7 on 2023-07-07 14:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0004_alter_paymentcard_pay_token'),
        ('bookings', '0006_booking_is_cancelled'),
    ]

    operations = [
        migrations.AddField(
            model_name='depositreplenishment',
            name='booking',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replenishments', to='bookings.booking'),
        ),
        migrations.AddField(
            model_name='depositreplenishment',
            name='payment_card',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replenishments', to='payments.paymentcard'),
        ),
    ]