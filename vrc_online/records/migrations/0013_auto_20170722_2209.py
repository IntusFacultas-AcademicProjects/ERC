# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-23 02:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0012_auto_20170722_2158'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calendarevent',
            name='medicine',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='events', to='records.Medicine'),
        ),
    ]
