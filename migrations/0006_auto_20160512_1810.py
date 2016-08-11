# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import xmodule_django.models


class Migration(migrations.Migration):

    dependencies = [
        ('course_groups', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('slam', '0005_auto_20160506_1842'),
    ]

    operations = [
        migrations.CreateModel(
            name='Participant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_key', xmodule_django.models.CourseKeyField(max_length=255, db_index=True)),
                ('wristband_id', models.CharField(db_index=True, max_length=16, choices=[(b'test', b'test purposes'), (b'000780A7BFD4', b'000780A7BFD4'), (b'000780A7C00F', b'000780A7C00F'), (b'000780A7BA8D', b'000780A7BA8D'), (b'000780A7C007', b'000780A7C007'), (b'000780A7BFF3', b'000780A7BFF3'), (b'000780A7BF7F', b'000780A7BF7F'), (b'000780A7BBC0', b'000780A7BBC0'), (b'0007801F8DB5', b'0007801F8DB5'), (b'000780A7BBC6', b'000780A7BBC6'), (b'000780A7BB26', b'000780A7BB26'), (b'000780A7BF63', b'000780A7BF63'), (b'000780A7BF73', b'000780A7BF73')])),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PCI',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_key', xmodule_django.models.CourseKeyField(max_length=255, db_index=True)),
                ('PCI', models.CharField(default=b'DA', max_length=8, db_index=True, choices=[(b'DA', b'Directional Agreement'), (b'SM', b'Signal Matching'), (b'IDM', b'Instantaneous Derivative Matching'), (b'PCC', b"Pearson's Correlation Coefficient")])),
                ('value', models.TextField()),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('cohort', models.ForeignKey(to='course_groups.CourseUserGroup')),
            ],
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_key', xmodule_django.models.CourseKeyField(max_length=255, db_index=True)),
                ('start', models.FloatField(db_index=True)),
                ('end', models.FloatField()),
                ('location', models.CharField(default=b'school', max_length=16, choices=[(b'LeaForum', b'LeaForum Laboratory'), (b'school', b"Student's school")])),
                ('type', models.CharField(default=b'exam', max_length=16, choices=[(b'lesson', b'Regular course lesson'), (b'exam', b'Exam session')])),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_modified', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.AlterField(
            model_name='script',
            name='created',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AlterField(
            model_name='script',
            name='last_modified',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AlterField(
            model_name='wristband',
            name='created',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AlterField(
            model_name='wristband',
            name='last_modified',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AlterField(
            model_name='wristband',
            name='value',
            field=models.FloatField(),
        ),
        migrations.AlterUniqueTogether(
            name='session',
            unique_together=set([('course_key', 'start')]),
        ),
        migrations.AddField(
            model_name='pci',
            name='session',
            field=models.ForeignKey(to='slam.Session'),
        ),
        migrations.AlterUniqueTogether(
            name='pci',
            unique_together=set([('course_key', 'cohort', 'PCI', 'session')]),
        ),
        migrations.AlterUniqueTogether(
            name='participant',
            unique_together=set([('course_key', 'user', 'wristband_id')]),
        ),
    ]
