# Generated by Django 4.1.7 on 2023-05-01 13:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clubs', '0003_rename_club_clubcomputer_club_branch_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='club',
            options={'verbose_name': 'Компьютерный Клуб', 'verbose_name_plural': 'Компьютерные Клубы'},
        ),
        migrations.AlterModelOptions(
            name='clubbranch',
            options={'verbose_name': 'Филиал Клуба', 'verbose_name_plural': 'Филиалы Клубов'},
        ),
        migrations.RemoveField(
            model_name='clubuserinfo',
            name='password',
        ),
        migrations.AddField(
            model_name='clubbranch',
            name='ip_address',
            field=models.URLField(default='http://127.0.0.1:8000', verbose_name='Белый IP адрес филиала'),
        ),
        migrations.AddField(
            model_name='clubcomputer',
            name='gizmo_hostname',
            field=models.CharField(max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='clubcomputer',
            name='gizmo_id',
            field=models.IntegerField(null=True),
        ),
    ]
