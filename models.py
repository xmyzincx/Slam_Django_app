from django.db import models
from django.contrib.auth.models import User
# from django.utils import timezone
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.course_groups.cohorts import CourseUserGroup
from xmodule_django.models import CourseKeyField


# Django documentation notes
# null is a field option referred to the DATABASE (backend)
# blank is a field option referred to a FORM (front-end)
#
# Datetimefield.auto_now: useful for "last-modified" timestamps. Only updated when calling Model.save()
# Datetimefield.auto_now_add: useful for "created" timestamps
#
# The value of the field. Defaults to None dumped as json
# value = models.TextField(default='null')

# Synchronization of values for individual participants
class Individual_sync(models.Model):
    user = models.ForeignKey(User)
    timestamp = models.FloatField(null=False, db_index=True)
    temperature = models.FloatField(null=True, db_index=False)
    EDA = models.FloatField(null=True, db_index=False)
    BVP = models.FloatField(null=False, db_index=False)
    HR = models.FloatField(null=True, db_index=False)
    acc_x = models.FloatField(null=True, db_index=False)
    acc_y = models.FloatField(null=True, db_index=False)
    acc_z = models.FloatField(null=True, db_index=False)
    edx_event = models.TextField(null=True, db_index=False)
    created = models.DateTimeField(auto_now_add=True, null=True, db_index=False)
    last_modified = models.DateTimeField(auto_now=True, null=True, db_index=False)

    class Meta:
        unique_together = (('user', 'timestamp'),)

    def __unicode__(self):
        return unicode(repr(self))


# Data collected by the wristband
class Wristband(models.Model):
    # 12 possible wristband ids
    # MAC addresses
    WRISTBAND_IDS = (
        ('test', 'test purposes'),
        ('000780A7BFD4', '000780A7BFD4'),
        ('000780A7C00F', '000780A7C00F'),
        ('000780A7BA8D', '000780A7BA8D'),
        ('000780A7C007', '000780A7C007'),
        ('000780A7BFF3', '000780A7BFF3'),
        ('000780A7BF7F', '000780A7BF7F'),
        ('000780A7BBC0', '000780A7BBC0'),
        ('0007801F8DB5', '0007801F8DB5'),
        ('000780A7BBC6', '000780A7BBC6'),
        ('000780A7BB26', '000780A7BB26'),
        ('000780A7BF63', '000780A7BF63'),
        ('000780A7BF73', '000780A7BF73'),
    )

    wristband_id = models.CharField(max_length=16, choices=WRISTBAND_IDS, default='test', null=False, db_index=True)

    SIGNALS = (('temperature', 'Temperature'),
               ('EDA', 'Electrodermal activity'),
               ('BVP', 'Blood Volume Pulse'),
               ('Acc_x', 'Acc_x'),
               ('Acc_y', 'Acc_y'),
               ('Acc_z', 'Acc_z'),
               ('IBI', 'Interbeat Interval'),
               ('HR', 'Heart rate'),
               )

    signal = models.CharField(max_length=16, choices=SIGNALS, default='EDA', null=False, db_index=True)
    timestamp = models.FloatField(null=False, db_index=True)
    value = models.FloatField(null=False, db_index=False)
    created = models.DateTimeField(auto_now_add=True, null=True, db_index=False)
    last_modified = models.DateTimeField(auto_now=True, null=True, db_index=False)

    class Meta:
        unique_together = (('wristband_id', 'signal', 'timestamp'),)

    def __unicode__(self):
        return unicode(repr(self))


# SLAM experiment participant
# Complements the information of Django's User model
class Participant(models.Model):
    course_key = CourseKeyField(max_length=255, null=False, db_index=True)
    user = models.ForeignKey(User)
    wristband_id = models.CharField(max_length=16, choices=Wristband.WRISTBAND_IDS, null=False, db_index=True)
    created = models.DateTimeField(auto_now_add=True, null=True, db_index=False)
    last_modified = models.DateTimeField(auto_now=True, null=True, db_index=False)

    class Meta:
        unique_together = (('course_key', 'wristband_id'),)

    def __unicode__(self):
        return unicode(repr(self))


# Course lesson calendar
class Session(models.Model):
    Locations = (('LeaForum', 'LeaForum Laboratory'),
                 ('school', 'Student\'s school'),
                 )
    Types = (('lesson', 'Regular course lesson'),
             ('exam', 'Exam session'),
             )

    course_key = CourseKeyField(max_length=255, null=False, db_index=True)
    start = models.FloatField(null=False, db_index=True)
    end = models.FloatField(null=False, db_index=False)
    location = models.CharField(max_length=16, choices=Locations, default='school', null=False, db_index=False)
    type = models.CharField(max_length=16, choices=Types, default='exam', null=False, db_index=False)
    checked_dashboard = models.BooleanField(default=False, db_index=False)
    answered_survey = models.CharField(max_length=32, default='no', null=True, db_index=False)
    created = models.DateTimeField(auto_now_add=True, null=True, db_index=False)
    last_modified = models.DateTimeField(auto_now=True, null=True, db_index=False)

    class Meta:
        unique_together = (('course_key', 'start'),)

    def __unicode__(self):
        return unicode(repr(self))


# Calculated Physiological Coupling Indices
class PCI(models.Model):
    PCIS = (('DA', 'Directional Agreement'),
            ('SM', 'Signal Matching'),
            ('IDM', 'Instantaneous Derivative Matching'),
            ('PCC', 'Pearson\'s Correlation Coefficient'),
            )

    course_key = CourseKeyField(max_length=255, null=False, db_index=True)
    cohort = models.ForeignKey(CourseUserGroup)
    session = models.ForeignKey(Session)
    PCI = models.CharField(max_length=8, choices=PCIS, default='DA', null=False, db_index=True)
    # value: list containing the group PCI, and then pairwise PCI for as many possible pairings in the group
    # example: for group ABC value = [PCI_ABC, PCI_AB, PCI_BC, PCI_CA]
    value = models.TextField(null=False, db_index=False)
    created = models.DateTimeField(auto_now_add=True, null=True, db_index=False)
    last_modified = models.DateTimeField(auto_now=True, null=True, db_index=False)

    class Meta:
        unique_together = (('course_key', 'cohort', 'PCI', 'session'),)

    def __unicode__(self):
        return unicode(repr(self))


# Results from the script (course surveys) ready to be visualized
class Script(models.Model):
    course_key = CourseKeyField(max_length=255, null=False, db_index=True)
    cohort = models.ForeignKey(CourseUserGroup)
    # script results ready for visualization. Results include collaboration, cognition, motivation and emotion.
    results = models.TextField(db_index=False)
    created = models.DateTimeField(auto_now_add=True, null=True, db_index=False)
    last_modified = models.DateTimeField(auto_now=True, null=True, db_index=False)

    class Meta:
        unique_together = (('course_key', 'cohort'),)

    def __unicode__(self):
        return unicode(repr(self))
