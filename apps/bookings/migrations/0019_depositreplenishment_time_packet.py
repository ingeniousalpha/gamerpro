# Generated by Django 4.1.7 on 2024-01-17 18:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clubs', '0032_alter_clubbranchadmin_options_and_more'),
        ('bookings', '0018_alter_booking_uuid'),
    ]

    operations = [
        migrations.AddField(
            model_name='depositreplenishment',
            name='time_packet',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='replenishments', to='clubs.clubtimepacket'),
        ),
    ]
