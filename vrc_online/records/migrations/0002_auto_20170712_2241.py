# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-13 02:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='medicine',
            name='notes',
            field=models.TextField(blank=True, max_length=256, null=True),
        ),
    ]
