# Generated by Django 4.1.7 on 2024-11-26 09:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clubs', '0060_merge_20241126_1418'),
    ]

    operations = [
        migrations.RenameField(
            model_name='clubtimepacketgroup',
            old_name='gizmo_id',
            new_name='outer_id',
        ),
    ]