# Generated by Django 2.1.3 on 2018-11-05 16:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('daiquiri_auth', '0011_meta'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='profile',
            options={'ordering': ('user__last_name', 'user__last_name', 'user__username'), 'verbose_name': 'Profile', 'verbose_name_plural': 'Profiles'},
        ),
    ]