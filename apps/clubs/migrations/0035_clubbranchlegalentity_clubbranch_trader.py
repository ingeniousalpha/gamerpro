# Generated by Django 4.1.7 on 2024-02-16 04:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clubs', '0034_clubbranch_trader_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClubBranchLegalEntity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=256)),
                ('code', models.CharField(default='', max_length=30)),
            ],
        ),
        migrations.AddField(
            model_name='clubbranch',
            name='trader',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='club_branches', to='clubs.clubbranchlegalentity'),
        ),
    ]