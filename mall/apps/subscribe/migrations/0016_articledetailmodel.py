# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-05-16 09:15
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('subscribe', '0015_auto_20190516_1439'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArticledetailModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user', to='subscribe.User', verbose_name='用户')),
            ],
            options={
                'verbose_name_plural': '文章关注表',
                'verbose_name': '文章关注表',
                'db_table': 'up_bids_user_follow',
            },
        ),
    ]
