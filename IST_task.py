from __future__ import division, absolute_import

import datetime
import time

from courseware.courses import get_course_by_id
from django.db.models import Max
from django.db.models import Q
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.course_groups.cohorts import get_course_cohorts, get_group_info_for_cohort
from slam.models import Wristband, PCI, Session, Participant
from itertools import combinations
from django.db import connection


def Individual_sync_table():
    # get edX courses in this instance. List of XModuleDescriptors
    course_keys = CourseOverview.get_all_course_keys()

    for course_key in course_keys:
        # course descriptor
        course = get_course_by_id(course_key, depth=None)

        # Here it is assumed that session will provide a timestamp (in unix format)
        # on which the session took place
        # for session in all_sessions_per_course
        course_sessions = Session.objects.filter(course_key=course_key)

        # get a list of all course cohorts (CourseUserGroup objects) or empty list if no cohort
        course_cohorts = get_course_cohorts(course=course, assignment_type='manual')

        if course_cohorts:
            for cohort in course_cohorts:
                # Until this point, sorted_cohort_users list has all the users
                id_email_list = [(u.id, u.email) for u in cohort.users.all().order_by('email')]
                for session in course_sessions:
                    for user in id_email_list:
                        user_wb_id = get_wristband_id(course_key, user)
                        if user_wb_id:
                            # After this point, only those users will be entertained who have E4 wristband
                            last_bvp_ts = get_latest_BVP_ts(user_wb_id, session.start, session.end)
                            if last_bvp_ts is not None:
                                print "--------------"
                                print "Valid Data"
                                print course.id
                                print 'Cohort ID: ' + str(cohort.id)
                                print 'USER ID: ' + str(user[0])
                                print 'Session ID: ' + str(session.id)
                                print 'Session start time: ' + str(session.start)
                                print 'Latest BVP timestamp: ' + str(last_bvp_ts)
                                print 'User wristband ID: ' + user_wb_id
                                print 'Wristband_id size: ' + str(len(user_wb_id))
                                print "--------------"

                                query = IST_query()
                                cursor = connection.cursor()
                                cursor.execute(query, [user[0], user_wb_id, session.start, last_bvp_ts])
                                cursor.close()
                                connection.commit()
                            else:
                                print "--------------"
                                print 'User does not have valid data for this session in Wristband table.'
                                print course.id
                                print 'Cohort ID: ' + str(cohort.id)
                                print 'USER ID: ' + str(user[0])
                                print 'Session ID: ' + str(session.id)
                                print 'Session start time: ' + str(session.start)
                                print 'Session end time: ' + str(session.end)
                                print 'User wristband ID: ' + user_wb_id
                                print 'Wristband_id size: ' + str(len(user_wb_id))
                                print "--------------"
                        else:
                            print 'User does not have wristband.'


def IST_query():

    squery = "insert into edxapp.slam_individual_sync \
(user_id, `timestamp`, temperature, EDA, BVP, HR, acc_x, acc_y, acc_z) \
select * from \
((select %s as User_ID, `timestamp`, \
group_concat(case when `signal`='TEMP' then `value` end) as Temperature, \
group_concat(case when `signal`='EDA' then `value` end) as EDA, \
group_concat(case when `signal`='BVP' then `value` end) as BVP, \
group_concat(case when `signal`='HR' then `value` end) as HR, \
group_concat(case when `signal`='Acc_x' then `value` end) as Acc_x, \
group_concat(case when `signal`='Acc_y' then `value` end) as Acc_y, \
group_concat(case when `signal`='Acc_z' then `value` end) as Acc_z \
from edxapp.slam_wristband as wbt \
where not (`signal`='IBI') and \
wristband_id=%s \
and `timestamp`>=%s and `timestamp`<=%s \
group by timestamp) as user1);"

    return squery


# This function will take care if the user does not have E4 wristband.
def get_wristband_id(course_key, user):
    try:
        wb_id = str(Participant.objects.get(course_key=course_key, user_id=user[0]).wristband_id)
    except Participant.DoesNotExist:
        return
    return wb_id.strip()


def get_latest_BVP_ts(u_wb_id, start_time, end_time):
    ts = None
    print '*** In latest_BVP_ts getter function ***'
    try:
        val_criteria = Q(wristband_id=u_wb_id) & Q(timestamp__gte=start_time) & Q(timestamp__lte=end_time) & Q(signal='BVP')
        queryset = Wristband.objects.filter(val_criteria)
        print queryset.query
        ts = queryset.aggregate(Max('timestamp')).get('timestamp__max')
        print 'Timestamp value: ' + str(ts)
        if ts is None:
            ts = get_latest_BVP_ts_v2(u_wb_id, start_time, end_time)
            print 'Second try to get ts value: ' + str(ts)
    except Exception, e:
        print str(e)
        print 'Exception occured. Timestamp value is None'
    print '***************************'
    return ts


def get_latest_BVP_ts_v2(u_wb_id, start_time, end_time):
    cursor = connection.cursor()
    query = "select max(timestamp) from edxapp.slam_wristband where wristband_id=%s and `timestamp`>=%s and `timestamp`<=%s and `signal`='BVP'"
    cursor.execute(query, [u_wb_id, start_time, end_time])
    ts = cursor.fetchone()
    cursor.close()
    print 'In version 2: ' + str(ts[0])
    return ts[0]

