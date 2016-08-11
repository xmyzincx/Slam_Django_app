# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('slam', '0003_auto_20160506_1102'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='wristband',
            name='created',
        ),
        migrations.RemoveField(
            model_name='wristband',
            name='last_modified',
        ),
    ]
