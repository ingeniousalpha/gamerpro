# Generated by Django 4.1.7 on 2023-10-24 03:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0006_payment_replenishment_alter_payment_booking'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='status',
            field=models.CharField(choices=[('0', 'Транзакция Создана'), ('1', 'Захолдированы средства'), ('2', 'Разхолдированы средства'), ('3', 'Оплачено'), ('4', 'Возвращено'), ('8', 'В обработке'), ('99', 'Ошибка')], default='0', max_length=20),
        ),
        migrations.AlterField(
            model_name='paymentstatustransition',
            name='status',
            field=models.CharField(choices=[('0', 'Транзакция Создана'), ('1', 'Захолдированы средства'), ('2', 'Разхолдированы средства'), ('3', 'Оплачено'), ('4', 'Возвращено'), ('8', 'В обработке'), ('99', 'Ошибка')], default='0', max_length=256),
        ),
    ]