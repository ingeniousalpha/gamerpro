# Generated by Django 4.1.7 on 2024-01-04 08:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clubs', '0030_clubtimepacket_club_computer_group'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClubBranchAdmin',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mobile_phone', models.CharField(max_length=12)),
                ('tg_chat_id', models.CharField(blank=True, max_length=128, null=True)),
                ('tg_username', models.CharField(blank=True, max_length=128, null=True)),
                ('club_branch', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='admins', to='clubs.clubbranch')),
            ],
        ),
    ]
