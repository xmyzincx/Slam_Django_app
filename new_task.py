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
                for user in id_email_list:
                    user_wb_id = get_wristband_id(course_key, user)
                    # After this point, only those users will be entertained who have E4 wristband
                    if user_wb_id:
                        for session in course_sessions:
                            print "--------------"
                            print cohort
                            print user
                            print session
                            print user_wb_id
                            print "--------------"

                            #cursor = connection.cursor()
                            #cursor.execute("")


def IST_query(session, cohort_id, wb_id):
    session_id = session[0]
    session_start_time = session.start
    session_end_time = session.end
    query = "select * from \
    ((select '" + session_id + "' as Session_ID, '" + cohort_id + "' as Cohort_ID, wristband_id, timestamp Unix_timestamp, from_unixtime(timestamp, '%d.%m.%Y') `Date`, from_unixtime(timestamp, '%h.%i.%s') `Time`,\
    group_concat(case when `signal`='TEMP' then `value` end) as Temperature, \
    group_concat(case when `signal`='EDA' then `value` end) as EDA, \
    group_concat(case when `signal`='BVP' then `value` end) as BVP, \
    group_concat(case when `signal`='Acc_x' then `value` end) as Acc_x, \
    group_concat(case when `signal`='Acc_y' then `value` end) as Acc_y, \
    group_concat(case when `signal`='Acc_z' then `value` end) as Acc_z \
    group_concat(case when `signal`='HR' then `value` end) as HR, \
    from edxapp.slam_wristband as wbt \
    where wristband_id='" + wb_id + "' \
    and `timestamp`>=" + session_start_time + " and `timestamp`<=" + session_end_time + " \
    group by timestamp) as user1)"
    return query


# This function will take care if the user does not have E4 wristband.
def get_wristband_id(course_key, user):
    try:
        wb_id = Participant.objects.get(course_key=course_key, user_id=user[0]).wristband_id
    except Participant.DoesNotExist:
        return
    return wb_id
