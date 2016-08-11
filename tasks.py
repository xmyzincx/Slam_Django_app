from __future__ import absolute_import

from celery.task import task  # current_task  # pylint: disable=no-name-in-module
from celery.exceptions import RetryTaskError  # pylint: disable=no-name-in-module, import-error
from courseware.courses import get_course_by_id
from datetime import datetime
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.course_groups.cohorts import get_course_cohorts, get_group_info_for_cohort
from slam.models import Script, Session # , Wristband
from slam.utils import *
from time import time
from util.views import ensure_valid_course_key

import json
import logging

log = logging.getLogger('edx.celery.task')


# TODO Celery task scheduling is not working. Hypothesis: naming inconsistency.
# @task
# @ensure_valid_course_key
def update_survey_data(course_key=None, from_scratch=0):
    print "Update starting: " + str(datetime.now())
    # get edX courses in this instance. List of XModuleDescriptors
    if course_key:
        # Ensure valid course key. The @ensure_valid_course_key decorator was first used but it is incompatible with
        # the option of calling the function without arguments.
        try:
            course_keys = [CourseKey.from_string(course_key)]
        except InvalidKeyError:
            print "Error: " + course_key + " is an invalid course key."
            return
    else:
        course_keys = CourseOverview.get_all_course_keys()
    for course_key in course_keys:
        print "Processing course key " + str(course_key) + ": " + str(datetime.now())
        # course descriptor
        course = get_course_by_id(course_key, depth=None)
        print "  Course obtained: " + str(datetime.now())
        # get a list of all course cohorts (CourseUserGroup objects) or empty list if no cohort
        course_cohorts = get_course_cohorts(course=course, assignment_type='manual')
        print "    Course cohorts obtained: " + str(datetime.now())
        if course_cohorts:
            # obtain the surveys in the course
            # the surveys are sorted as they appear in the course
            # list of SurveyBlockWithMixins objects
            surveys_in = get_blocks_by_type(course, block_type="survey")
            print "    Course surveys obtained: " + str(datetime.now())
            if surveys_in:
                # the course has at least a survey
                # EdX structures collection in MongoDB
                structures_collection = get_mongodb_connection()['modulestore.structures']
                if not from_scratch:
                    current_time = int(time())
                    course_sessions = Session.objects.filter(course_key=course_key).order_by('start')
                    course_sessions = course_sessions.values_list('start', flat=True) if course_sessions else []
                    if course_sessions:
                        next_session = next(start for start in course_sessions if start > current_time)
                        # -1 because the first session was introductory and doesn't count
                        past_sessions = list(course_sessions).index(next_session) -1
                    else:
                        past_sessions = 0
                    print "    Past sessions: " + str(past_sessions)
                surveys_to_delete = []
                for cohort in course_cohorts:
                    surveys_in_original = surveys_in
                    print "      Processing cohort " + str(cohort) + ": " + str(datetime.now())
                    (group_id, partition_id) = get_group_info_for_cohort(cohort)
                    survey_data = []
                    if not from_scratch:
                        try:
                            last_computed_results = Script.objects.get(course_key=course_key, cohort=cohort).results
                            print "      Last computed results: " + str(last_computed_results)
                            last_computed_survey = eval(last_computed_results)[-1][0]
                        except (Script.DoesNotExist, NameError, IndexError):
                            last_computed_survey = 0
                        if past_sessions and last_computed_survey:
                            low_index = len(course_cohorts) * last_computed_survey - 1
                            high_index = len(course_cohorts) * past_sessions * 2 - 1
                            print "      Low index: " + str(low_index) + ". High index: " + str(high_index)
                            surveys_in = surveys_in[low_index:high_index]
                    if surveys_to_delete:
                        surveys_in_aux = [s for s in surveys_in if s.location.name not in surveys_to_delete]
                        surveys_in = surveys_in_aux
                    if surveys_in:
                        for survey in surveys_in:
                            print "        Processing survey: " + str(datetime.now())
                            block_id = survey.location.name
                            # line below is the most expensive in this task
                            survey_fields = get_survey_fields(structures_collection, block_id)
                            try:
                                # check if the survey is in the cohort course path
                                this_cohort_survey = survey_fields["group_access"][str(partition_id)].count(group_id)
                                # questions in the survey
                                questions = survey_fields["questions"]
                                # available answers in the survey
                                answers = survey_fields["answers"]
                                print "        Survey in cohort path. " + str(datetime.now())
                            except KeyError:
                                this_cohort_survey = None
                                questions = []
                                answers = []
                            if this_cohort_survey and len(questions) == 4 and len(answers) == 10:
                                survey_data = [[] for i in range(0, len(questions))] if not survey_data else survey_data
                                for i in range(0, len(questions)):
                                    cohort_users_answers = []
                                    for cohort_user in cohort.users.all():
                                        user_answer = get_user_survey_answer(course_key,
                                                                             cohort_user,
                                                                             survey.location,
                                                                             questions,
                                                                             answers,
                                                                             i)
                                        print "          Answers obtained for student " + str(cohort_user.username) +\
                                              ": " + str(datetime.now())
                                        if user_answer:
                                            cohort_users_answers.append(user_answer)
                                    answer_value = min(cohort_users_answers) if cohort_users_answers else None
                                    survey_data[i].append(answer_value)
                                # if the survey belongs to his cohort, we should remove it so speed up searches
                                # for next cohorts
                                surveys_to_delete.append(survey.location.name)
                        if len(survey_data) >= 1:
                            if (not from_scratch) and last_computed_survey:
                                # Prepare the array in the Google Charts arrayToDataTable format
                                survey_data = map(lambda *a: list(a), *survey_data)
                                aux_surveydata = eval(last_computed_results)
                                for i in range(0, len(survey_data)):
                                    if survey_data[i].count(None) < len(survey_data[i]):
                                        # include survey number
                                        survey_data[i].insert(0, last_computed_survey + i + 1)
                                        aux_surveydata.append(survey_data[i])
                                survey_data = aux_surveydata
                            else:
                                # Prepare the array in the Google Charts arrayToDataTable format
                                survey_data = survey_data_to_chart_format(survey_data)
                        # store results for course and cohort in Script table
                        save_script_results(course_key, cohort, survey_data)
                        print "            Results saved to Script table: " + str(datetime.now())
                    surveys_in = surveys_in_original


# @task()
# def test_4_celery():
#         field_values = {
#         'wristband_id': '000780A7BFD4',
#         'signal': 'EDA',
#         'timestamp': time.time(),
#         'value': '2.0123123'
#         }
#         tldat = Wristband(**field_values)
#         try:
#             tldat.save()
#             log.info("Data saved successfully into the database.")
#         except Exception as e:  # pylint: disable=broad-except
#             #print '%s (%s)' % (e.message, type(e))
#             log.exception("Exception occurred while writing data into the database.")
#             #return JsonResponse({'mesg': 'Values not saved'})
