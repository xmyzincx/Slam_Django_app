# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Participant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('wristband_id', models.CharField(default=b'null', max_length=16, null=True, db_index=True, choices=[(b'000780A7BFD4', b'000780A7BFD4'), (b'000780A7C00F', b'000780A7C00F'), (b'000780A7BA8D', b'000780A7BA8D'), (b'000780A7C007', b'000780A7C007'), (b'000780A7BFF3', b'000780A7BFF3'), (b'000780A7BF7F', b'000780A7BF7F'), (b'000780A7BBC0', b'000780A7BBC0'), (b'0007801F8DB5', b'0007801F8DB5'), (b'000780A7BBC6', b'000780A7BBC6'), (b'000780A7BB26', b'000780A7BB26'), (b'000780A7BF63', b'000780A7BF63'), (b'000780A7BF73', b'000780A7BF73')])),
                ('created', models.DateTimeField(db_index=True, auto_now_add=True, null=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Wristband',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('wristband_id', models.CharField(default=b'null', max_length=32, null=True, db_index=True, choices=[(b'000780A7BFD4', b'000780A7BFD4'), (b'000780A7C00F', b'000780A7C00F'), (b'000780A7BA8D', b'000780A7BA8D'), (b'000780A7C007', b'000780A7C007'), (b'000780A7BFF3', b'000780A7BFF3'), (b'000780A7BF7F', b'000780A7BF7F'), (b'000780A7BBC0', b'000780A7BBC0'), (b'0007801F8DB5', b'0007801F8DB5'), (b'000780A7BBC6', b'000780A7BBC6'), (b'000780A7BB26', b'000780A7BB26'), (b'000780A7BF63', b'000780A7BF63'), (b'000780A7BF73', b'000780A7BF73')])),
                ('signal', models.CharField(default=b'EDA', max_length=16, db_index=True, choices=[(b'temperature', b'temperature'), (b'EDA', b'EDA'), (b'BVP', b'BVP'), (b'Acc_x', b'Acc_x'), (b'Acc_y', b'Acc_y'), (b'Acc_z', b'Acc_z'), (b'IBI', b'IBI')])),
                ('timestamp', models.FloatField(db_index=True)),
                ('value', models.FloatField(db_index=True)),
                ('created', models.DateTimeField(db_index=True, auto_now_add=True, null=True)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='wristband',
            unique_together=set([('wristband_id', 'signal', 'timestamp')]),
        ),
    ]
