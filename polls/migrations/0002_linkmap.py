# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-13 13:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LinkMap',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('global_link', models.CharField(max_length=500)),
                ('local_link', models.CharField(max_length=500)),
            ],
        ),
    ]
