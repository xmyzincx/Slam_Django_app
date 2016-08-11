# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import xmodule_django.models


class Migration(migrations.Migration):

    dependencies = [
        ('course_groups', '0001_initial'),
        ('slam', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Script',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_key', xmodule_django.models.CourseKeyField(max_length=255, db_index=True)),
                ('results', models.TextField()),
                ('created', models.DateTimeField(db_index=True, auto_now_add=True, null=True)),
                ('cohort', models.ForeignKey(to='course_groups.CourseUserGroup')),
            ],
        ),
        migrations.RemoveField(
            model_name='participant',
            name='user',
        ),
        migrations.AlterField(
            model_name='wristband',
            name='wristband_id',
            field=models.CharField(default=b'null', max_length=16, null=True, db_index=True, choices=[(b'000780A7BFD4', b'000780A7BFD4'), (b'000780A7C00F', b'000780A7C00F'), (b'000780A7BA8D', b'000780A7BA8D'), (b'000780A7C007', b'000780A7C007'), (b'000780A7BFF3', b'000780A7BFF3'), (b'000780A7BF7F', b'000780A7BF7F'), (b'000780A7BBC0', b'000780A7BBC0'), (b'0007801F8DB5', b'0007801F8DB5'), (b'000780A7BBC6', b'000780A7BBC6'), (b'000780A7BB26', b'000780A7BB26'), (b'000780A7BF63', b'000780A7BF63'), (b'000780A7BF73', b'000780A7BF73')]),
        ),
        migrations.DeleteModel(
            name='Participant',
        ),
        migrations.AlterUniqueTogether(
            name='script',
            unique_together=set([('course_key', 'cohort')]),
        ),
    ]
