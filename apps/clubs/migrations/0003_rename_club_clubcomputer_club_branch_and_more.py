# Generated by Django 4.1.7 on 2023-04-24 10:05

import apps.clubs.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clubs', '0002_alter_clubcomputer_hall_type_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='clubcomputer',
            old_name='club',
            new_name='club_branch',
        ),
        migrations.RenameField(
            model_name='clubuserinfo',
            old_name='club',
            new_name='club_branch',
        ),
        migrations.CreateModel(
            name='ClubBranchProperty',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hall_type', models.CharField(choices=[('STANDARD', 'Стандарт'), ('VIP', 'ВИП')], default='STANDARD', max_length=20)),
                ('name', models.CharField(max_length=100)),
                ('club_branch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='properties', to='clubs.clubbranch')),
            ],
            bases=(apps.clubs.models.HallTypesManagerMixin, models.Model),
        ),
        migrations.CreateModel(
            name='ClubBranchPrice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hall_type', models.CharField(choices=[('STANDARD', 'Стандарт'), ('VIP', 'ВИП')], default='STANDARD', max_length=20)),
                ('name', models.CharField(max_length=100)),
                ('price', models.IntegerField()),
                ('club_branch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prices', to='clubs.clubbranch')),
            ],
            bases=(apps.clubs.models.HallTypesManagerMixin, models.Model),
        ),
        migrations.CreateModel(
            name='ClubBranchHardware',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hall_type', models.CharField(choices=[('STANDARD', 'Стандарт'), ('VIP', 'ВИП')], default='STANDARD', max_length=20)),
                ('name', models.CharField(max_length=100)),
                ('club_branch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hardware', to='clubs.clubbranch')),
            ],
            bases=(apps.clubs.models.HallTypesManagerMixin, models.Model),
        ),
    ]
