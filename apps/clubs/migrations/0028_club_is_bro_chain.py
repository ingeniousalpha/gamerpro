# Generated by Django 4.1.7 on 2023-12-23 04:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clubs', '0027_alter_clubbranchuser_gizmo_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='club',
            name='is_bro_chain',
            field=models.BooleanField(default=False),
        ),
    ]
