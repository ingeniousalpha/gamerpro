# Generated by Django 4.1.7 on 2023-09-30 06:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clubs', '0021_clubtimepacketgroup_clubtimepacket'),
    ]

    operations = [
        migrations.AddField(
            model_name='clubtimepacket',
            name='priority',
            field=models.IntegerField(default=0),
        ),
    ]
