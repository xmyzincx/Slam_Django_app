# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('slam', '0002_auto_20160417_2035'),
    ]

    operations = [
        migrations.AddField(
            model_name='script',
            name='last_modified',
            field=models.DateTimeField(db_index=True, auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='wristband',
            name='last_modified',
            field=models.DateTimeField(db_index=True, auto_now=True, null=True),
        ),
        migrations.AlterField(
            model_name='wristband',
            name='wristband_id',
            field=models.CharField(default=b'test', max_length=16, db_index=True, choices=[(b'test', b'test purposes'), (b'000780A7BFD4', b'000780A7BFD4'), (b'000780A7C00F', b'000780A7C00F'), (b'000780A7BA8D', b'000780A7BA8D'), (b'000780A7C007', b'000780A7C007'), (b'000780A7BFF3', b'000780A7BFF3'), (b'000780A7BF7F', b'000780A7BF7F'), (b'000780A7BBC0', b'000780A7BBC0'), (b'0007801F8DB5', b'0007801F8DB5'), (b'000780A7BBC6', b'000780A7BBC6'), (b'000780A7BB26', b'000780A7BB26'), (b'000780A7BF63', b'000780A7BF63'), (b'000780A7BF73', b'000780A7BF73')]),
        ),
    ]
