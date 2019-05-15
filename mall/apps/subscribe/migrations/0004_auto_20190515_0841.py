# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-05-15 00:41
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('subscribe', '0003_bidsusersetting_remind_long_time'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bidsusersetting',
            name='mid',
        ),
        migrations.AddField(
            model_name='user',
            name='bids_set_id',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='bidset', to='subscribe.BidsUserSetting', verbose_name='订阅表'),
        ),
    ]
