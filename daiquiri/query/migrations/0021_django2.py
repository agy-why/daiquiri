# Generated by Django 2.1.3 on 2018-11-05 16:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('daiquiri_query', '0020_python3'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='downloadjob',
            options={'ordering': ('start_time',), 'verbose_name': 'DownloadJob', 'verbose_name_plural': 'DownloadJobs'},
        ),
        migrations.AlterModelOptions(
            name='example',
            options={'ordering': ('order',), 'verbose_name': 'Example', 'verbose_name_plural': 'Examples'},
        ),
        migrations.AlterModelOptions(
            name='queryarchivejob',
            options={'ordering': ('start_time',), 'verbose_name': 'QueryArchiveJob', 'verbose_name_plural': 'QueryArchiveJob'},
        ),
        migrations.AlterModelOptions(
            name='queryjob',
            options={'ordering': ('start_time',), 'verbose_name': 'QueryJob', 'verbose_name_plural': 'QueryJobs'},
        ),
    ]