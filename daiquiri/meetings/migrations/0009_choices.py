# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-07-03 13:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('daiquiri_meetings', '0008_slug_max_length'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participant',
            name='status',
            field=models.CharField(choices=[(b'ORGANIZER', 'organizer'), (b'DISCUSSION_LEADER', 'discussion leader'), (b'INVITED', 'invited'), (b'REGISTERED', 'registered'), (b'ACCEPTED', 'accepted'), (b'REJECTED', 'rejected'), (b'CANCELED', 'canceled')], help_text='Status of the participant.', max_length=32, verbose_name='Status'),
        ),
    ]
