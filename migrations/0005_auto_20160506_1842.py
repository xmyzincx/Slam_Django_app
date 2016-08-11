# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('slam', '0004_auto_20160506_1811'),
    ]

    operations = [
        migrations.AddField(
            model_name='wristband',
            name='created',
            field=models.DateTimeField(db_index=True, auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='wristband',
            name='last_modified',
            field=models.DateTimeField(db_index=True, auto_now=True, null=True),
        ),
    ]
