# Generated by Django 4.1.7 on 2023-05-01 13:08

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('clubs', '0004_alter_club_options_alter_clubbranch_options_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ClubUserInfo',
            new_name='ClubBranchUser',
        ),
    ]
