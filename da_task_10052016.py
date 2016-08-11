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

signal_type = 'EDA'
PCI_type = 'DA'
pair_num = 2


# users = ['0007801F8DB5', '000780A7BF63', '000780A7C007']

# users is the list of users in cohorts
# date must be in unix timestamp format e.g. 1428451200 is for "00:00:00, 8th April, 2015"
# 86400 are the number of seconds in a day

# TODO Fuse initial_run_PCI into the main task. The condition we check should be valid for both first run as well as
# TODO next runs. A parameter like "reset" should be available in case we want to re-compute values from scratch

# TODO Take into account that for pairwise cohorts, only group PCI is needed, e.g. for group AB we need [AB_PCI] and not [AB_PCI, AB_PCI]

# Initial run is for the very first time when PCI table is empty
def initial_run_PCI():
    # get edX courses in this instance. List of XModuleDescriptors
    course_keys = CourseOverview.get_all_course_keys()

    for course_key in course_keys:
        # course descriptor
        course = get_course_by_id(course_key, depth=None)

        # Here it is assumed that session will provide a timestamp (in unix format)
        # on which the session took place
        # for session in all_sessions_per_course
        # all_session_st_et = get_all_sessions_st_et_for_course_key(course_key)
        course_sessions = Session.objects.filter(course_key=course_key)

        # all_sessions = Session.objects.all()

        # get a list of all course cohorts (CourseUserGroup objects) or empty list if no cohort
        course_cohorts = get_course_cohorts(course=course, assignment_type='manual')

        if course_cohorts:
            for cohort in course_cohorts:
                # (group_id, partition_id) = get_group_info_for_cohort(cohort)
                # TODO check if cohort_user is a single user or a list of all users
                # print cohort.users.all()
                # print cohort.users.all().order_by('email')
                # sorted_cohort_users = get_sorted_cohort_users(cohort.users.all())
                # Until this point, sorted_cohort_users list has all the users
                user_id_list = [user.id for user in cohort.users.all().order_by('email')]
                wb_ids_list = get_wristband_ids_list(course_key, user_id_list)
                # After this point, only those users will be entertained who have E4 wristband

                if wb_ids_list:

                    for session in course_sessions:
                        # session_id = session[0]
                        session_start_time = session.start
                        session_end_time = session.end
                        DA_vals_list = []
                        DA_vals_list.append(compute_cohort_DA(wb_ids_list, session_start_time, session_end_time))
                        # Pairing rule: Input = [a, b, c, d], Output = [ab, ac, ad, bc, bd, cd]
                        cohort_users_combinations = list(combinations(wb_ids_list, pair_num))

                        for pairs in cohort_users_combinations:
                            DA_vals_list.append(compute_cohort_DA(list(pairs), session_start_time, session_end_time))

                        if not set(DA_vals_list) == set([None]):
                            update_PCI_table(course_key, session, PCI_type, DA_vals_list, cohort)
                        print DA_vals_list
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
                else:
                    continue


def schedule_run_PCI():
    last_PCI_updated = get_last_modified_timestamp_from_pcit()
    last_wristband_timestamp_added = get_last_timestamp_from_wbt()

    if last_PCI_updated is None:
        initial_run_PCI()
    elif last_PCI_updated <= last_wristband_timestamp_added:
        # get edX courses in this instance. List of XModuleDescriptors
        course_keys = CourseOverview.get_all_course_keys()

        for course_key in course_keys:
            # course descriptor
            course = get_course_by_id(course_key, depth=None)

            # Here it is assumed that session will provide a timestamp (in unix format)
            # on which the session took place
            # for session in all_sessions_per_course
            # all_session_st_et = get_all_sessions_st_et_for_course_key(course_key)
            course_sessions = Session.objects.filter(course_key=course_key)

            # get a list of all course cohorts (CourseUserGroup objects) or empty list if no cohort
            course_cohorts = get_course_cohorts(course=course, assignment_type='manual')

            if course_cohorts:
                for cohort in course_cohorts:
                    (group_id, partition_id) = get_group_info_for_cohort(cohort)
                    # TODO check if cohort_user is a single user or a list of all users
                    # unsorted_cohort_users = cohort.users.all()
                    # sorted_cohort_users = get_sorted_cohort_users(unsorted_cohort_users)
                    # Until this point, sorted_cohort_users list has all the users
                    user_id_list = [user.id for user in cohort.users.all().order_by('email')]
                    wb_ids_list = get_wristband_ids_list(course_key, user_id_list)
                    # After this point, only those users will be entertained who have E4 wristband

                    for session in course_sessions:
                        session_start_time = session.start
                        session_end_time = session.end
                        DA_vals_list = []

                        if not check_if_session_exists(course_key, session_id, group_id):
                            DA_vals_list.append(compute_cohort_DA(wb_ids_list, session_start_time, session_end_time))
                            # Pairing rule: Input = [a, b, c, d], Output = [ab, ac, ad, bc, bd, cd]
                            cohort_users_combinations = list(combinations(wb_ids_list, pair_num))

                            for pair in cohort_users_combinations:
                                DA_vals_list.append(
                                    compute_cohort_DA(list(pair), session_start_time, session_end_time))

                            if not set(DA_vals_list) == set([None]):
                                update_PCI_table(course_key, session_id, PCI_type, DA_vals_list, group_id)
                            print DA_vals_list
                        else:
                            continue


def update_PCI_table(course_key, session_id, temp_PCI_type, PCI_val, cohort_id):
    # store results for course and cohort in Script table
    kw_pci_data = {
        'course_key': course_key,
        'PCI': temp_PCI_type,
        'value': PCI_val,
        'cohort': cohort_id,
        'session': session_id
    }
    try:
        new_entry = PCI.objects.get(course_key=kw_pci_data['course_key'],
                                    cohort=kw_pci_data['cohort'], session=kw_pci_data['session'])
    except PCI.DoesNotExist:
        new_entry = PCI(**kw_pci_data)
    new_entry.save()
    return


# This function will compute Directional Agreement (in terms of percentage) between users.
# Number of users may vary.
def compute_cohort_DA(users, session_st, session_et):
    # user index
    u_index = 0
    count_ones = 0
    users_val_dict = {}
    users_directions_dict = {}
    DA_list = []

    syncd_timestamps = get_syncd_timestamps_list(users, session_st, session_et, signal_type)
    rows = len(get_signal_values_for_timestamp_list(users[0], syncd_timestamps, signal_type))
    columns = len(users)
    directions_matrix = [[0 for i in range(columns)] for j in range(rows)]

    for user_id in users:
        directions_list = []
        val_list = get_signal_values_for_timestamp_list(user_id, syncd_timestamps, signal_type)
        users_val_dict[user_id] = val_list

        for index in range(len(val_list) - 1):
            if val_list[index] > val_list[index + 1]:
                directions_list.append('u')
                directions_matrix[index][u_index] = 1

            elif val_list[index] < val_list[index + 1]:
                directions_list.append('d')
                directions_matrix[index][u_index] = 2

            elif val_list[index] == val_list[index + 1]:
                directions_list.append('e')
                directions_matrix[index][u_index] = 3

        users_directions_dict[user_id] = directions_list
        u_index += 1

    for index in range(len(directions_matrix)):
        if len(set(directions_matrix[index])) == 1:
            DA_list.append(1)
            count_ones += 1
        else:
            DA_list.append(0)

    cohort_DA = (count_ones/len(DA_list))*100 if DA_list else None
    # if DA_list:
    #     cohort_DA = (count_ones/len(DA_list))*100
    # else:
    #     return None

    return cohort_DA


def get_timestamps_list(w_id, start_time, end_time, temp_signal_type):
    t_criteria = Q(wristband_id=w_id) & Q(timestamp__gte=start_time) \
                 & Q(timestamp__lte=end_time) & Q(signal=temp_signal_type)
    timestamp_list = Wristband.objects.values_list('timestamp', flat=True).filter(t_criteria)
    return timestamp_list


# wbt = Wristband Table
def get_last_timestamp_from_wbt():
    last_wbts_value = (Wristband.objects.values_list().aggregate(Max('timestamp'))).values()[0]
    return last_wbts_value


# pcit = PCI Table
def get_last_modified_timestamp_from_pcit():
    last_sts_value = (PCI.objects.values_list().aggregate(Max('last_modified'))).values()[0]
    return last_sts_value


def check_if_session_exists(course_key, session_date, group_id):
    # store results for course and cohort in Script table
    kw_pci_data = {
        'course_key': course_key,
        'session': session_date,
        'cohort_id': group_id
    }
    try:
        PCI.objects.get(course_key=kw_pci_data['course_key'], cohort=kw_pci_data['cohort_id'],
                        session=kw_pci_data['session'])
        return True
    except PCI.DoesNotExist:
        return False


# This function will return the intersection of all timestamps between the set of users
def get_syncd_timestamps_list(users, start_time, end_time, temp_signal_type):
    # This list_of_timestamp_list will be the combination of timestamp list of all users.
    # In other words, it is a list of a list(timestamp_list).
    list_of_timestamp_list = []
    for u_id in users:
        list_of_timestamp_list.append(set(get_timestamps_list(u_id, start_time, end_time, temp_signal_type)))
    syncd_timestamp_list = set.intersection(*list_of_timestamp_list)

    return syncd_timestamp_list


def get_signal_values_for_timestamp_list(w_id, timestamp_list, temp_signal_type):
    val_list = []
    for timestamp_val in timestamp_list:
        val_criteria = Q(wristband_id=w_id) & Q(timestamp=timestamp_val) & Q(signal=temp_signal_type)
        val_list.append((Wristband.objects.values_list('value', flat=True).filter(val_criteria))[0])

    return val_list


# def get_all_sessions_st_et_for_course_key(course_key):
#     session_st_et_list = Session.objects.filter(Q(course_key=course_key)).values_list('id', 'start', 'end')
#
#     return session_st_et_list


# # Sorting rule is Ascending order: Input = [b, a, d, c], Output = [a, b, c, d]
# def get_sorted_cohort_users(us_users):
#     us_users_dict = {}
#     for user in us_users:
#         # TODO get proper function for getting emal address
#         us_users_dict[user] = 'get_email_address'
#     s_users = sorted(us_users_dict, key=us_users_dict.get)
#     return s_users


# This function will take care if the user does not have E4 wristband.
def get_wristband_ids_list(course_key, users):
    wb_id_list = []
    for user in users:
        try:
            wb_id = Participant.objects.get(course_key=course_key, user_id=user).wristband_id
            # wb_id = Participant.values_list('wristband_id').filter(Q(user_id = user))[0]
            wb_id_list.append(wb_id)
        except Participant.DoesNotExist:
            continue

    return wb_id_list
