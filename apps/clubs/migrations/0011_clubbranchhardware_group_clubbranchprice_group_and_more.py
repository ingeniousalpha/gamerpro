# Generated by Django 4.1.7 on 2023-05-02 13:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clubs', '0010_clubbranch_gizmo_payment_method'),
    ]

    operations = [
        migrations.AddField(
            model_name='clubbranchhardware',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='clubs.clubcomputergroup'),
        ),
        migrations.AddField(
            model_name='clubbranchprice',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='clubs.clubcomputergroup'),
        ),
        migrations.AddField(
            model_name='clubbranchproperty',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='clubs.clubcomputergroup'),
        ),
    ]
