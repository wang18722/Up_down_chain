# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-05-15 12:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscribe', '0008_auto_20190515_2043'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bids',
            name='areas_id',
            field=models.SmallIntegerField(verbose_name='地区地址'),
        ),
    ]