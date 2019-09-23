# Generated by Django 2.1.4 on 2019-06-05 15:00

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Record',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identifier', models.CharField(db_index=True, max_length=256, verbose_name='OAI identifier')),
                ('datestamp', models.DateField(db_index=True, verbose_name='OAI datestamp')),
                ('metadata_prefix', models.CharField(db_index=True, max_length=16, verbose_name='OAI metadataPrefix')),
                ('deleted', models.BooleanField(db_index=True, default=False, verbose_name='Deleted')),
            ],
            options={
                'verbose_name_plural': 'Records',
                'db_table': 'records',
                'ordering': ('-datestamp',),
                'verbose_name': 'Record',
            },
        ),
    ]