# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-05-21 00:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Area',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='省名称')),
                ('isDeleted', models.BooleanField(default=False, verbose_name='是否删除')),
            ],
            options={
                'verbose_name': '地区',
                'db_table': 'up_area',
                'verbose_name_plural': '地区',
            },
        ),
    ]
