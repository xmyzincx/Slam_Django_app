from __future__ import absolute_import
from celery.task import task
from courseware.courses import get_course_by_id
# from lms import CELERY_APP
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.course_groups.cohorts import get_course_cohorts, get_group_info_for_cohort
from slam.utils import *
import logging


log = logging.getLogger('edx.celery.task')


@task
def update_survey_data():
    # get edX courses in this instance. List of XModuleDescriptors
    course_keys = CourseOverview.get_all_course_keys()
    for course_key in course_keys:
        # course descriptor
        course = get_course_by_id(course_key, depth=None)
        # get a list of all course cohorts (CourseUserGroup objects) or empty list if no cohort
        course_cohorts = get_course_cohorts(course=course, assignment_type='manual')
        if course_cohorts:
            # obtain the surveys in the course
            # TODO surveys should be sorted by before-after pairs
            # the surveys are sorted as they appear in the course
            # list of SurveyBlockWithMixins objects
            surveys_in = get_blocks_by_type(course, block_type="survey")
            if surveys_in:
                # the course has at least a survey
                # EdX structures collection in MongoDB
                structures_collection = get_mongodb_connection()['modulestore.structures']
                for cohort in course_cohorts:
                    (group_id, partition_id) = get_group_info_for_cohort(cohort)
                    survey_data = []
                    surveys_to_delete = []
                    for survey in surveys_in:
                        # questions = None
                        block_id = survey.location.name
                        survey_fields = get_survey_fields(structures_collection, block_id)
                        try:
                            # check if the survey is in the cohort course path
                            this_cohort_survey = survey_fields["group_access"][str(partition_id)].count(group_id)
                        except KeyError:
                            this_cohort_survey = None
                        if this_cohort_survey:
                            # number of possible answers in the survey
                            answers = survey_fields["answers"]
                            # questions in the survey
                            questions = survey_fields["questions"]
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
                                    if user_answer:
                                        cohort_users_answers.append(user_answer)
                                answer_value = min(cohort_users_answers) if cohort_users_answers else None
                                survey_data[i].append(answer_value)
                            # if the survey belongs to his cohort, we should remove it so speed up searches
                            # for next cohorts
                            surveys_to_delete.append(survey)
                    if surveys_to_delete:
                        for survey_to_delete in surveys_to_delete:
                            surveys_in.remove(survey_to_delete)
                    if len(survey_data) >= 1:
                        # Prepare the array in the Google Charts arrayToDataTable format
                        survey_data = survey_data_to_chart_format(survey_data)
                    # store results for course and cohort in Script table
                    save_script_results(course_key, cohort, survey_data)

