# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-05-16 06:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscribe', '0014_auto_20190516_1438'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bidsusersetting',
            name='keywords_array',
            field=models.CharField(max_length=60, verbose_name='关注关键字'),
        ),
    ]
