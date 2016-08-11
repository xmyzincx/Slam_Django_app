# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('slam', '0006_auto_20160512_1810'),
    ]

    operations = [
        migrations.CreateModel(
            name='Individual_sync',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.FloatField(db_index=True)),
                ('temperature', models.FloatField(null=True)),
                ('EDA', models.FloatField(null=True)),
                ('BVP', models.FloatField()),
                ('HR', models.FloatField(null=True)),
                ('acc_x', models.FloatField(null=True)),
                ('acc_y', models.FloatField(null=True)),
                ('acc_z', models.FloatField(null=True)),
                ('edx_event', models.TextField(null=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='session',
            name='answered_survey',
            field=models.CharField(default=b'no', max_length=32, null=True),
        ),
        migrations.AddField(
            model_name='session',
            name='checked_dashboard',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='wristband',
            name='signal',
            field=models.CharField(default=b'EDA', max_length=16, db_index=True, choices=[(b'temperature', b'Temperature'), (b'EDA', b'Electrodermal activity'), (b'BVP', b'Blood Volume Pulse'), (b'Acc_x', b'Acc_x'), (b'Acc_y', b'Acc_y'), (b'Acc_z', b'Acc_z'), (b'IBI', b'Interbeat Interval'), (b'HR', b'Heart rate')]),
        ),
        migrations.AlterUniqueTogether(
            name='participant',
            unique_together=set([('course_key', 'wristband_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='individual_sync',
            unique_together=set([('user', 'timestamp')]),
        ),
    ]
