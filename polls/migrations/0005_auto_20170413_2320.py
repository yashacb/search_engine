# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-13 23:20
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0004_userclick_username'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='userclick',
            unique_together=set([('word', 'video_id', 'username')]),
        ),
    ]
