# -*- coding: utf-8 -*-

from courseware.courses import get_course_with_access, has_access, get_studio_url
from openedx.core.djangoapps.course_groups.cohorts import get_cohort, get_cohort_id
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render_to_response
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt #, ensure_csrf_cookie
# from django.views.decorators.http import require_POST
from opaque_keys.edx.keys import CourseKey
from rest_framework.generics import GenericAPIView
from slam.models import PCI, Script, Wristband
from slam.tasks import update_survey_data
from student.models import CourseEnrollment
# from util.json_request import expect_json
from util.views import ensure_valid_course_key

import json

# These are the fields to be stored in the database
LOGFIELDS = [
    'wristband_id',
    'signal',
    'timestamp',
    'value',
]


# This is the decorator to exempt cross-site request forgery.
@csrf_exempt
def sensor_data(request):
    if request.method == 'POST':
        rcvd_json_data = json.loads(request.body)
        # print rcvd_json_data
        field_values = {x: rcvd_json_data.get(x, '') for x in LOGFIELDS}
        # print field_values
        tldat = Wristband(**field_values)
        try:
            tldat.save()
        except Exception as e:  # pylint: disable=broad-except
            print '%s (%s)' % (e.message, type(e))
            return JsonResponse({'mesg': 'Values not saved'})
        return JsonResponse({'mesg': 'Success'})
    else:  # Other requests
        return HttpResponse("You're at empatica sensor data API. Invalid request.")


class SlamDashboardView(GenericAPIView):
    """
    View methods related to the teams dashboard.
    """

    def get(self, request, course_id):
        # celery_simulation = True
        # if celery_simulation:
        #     update_survey_data()

        user = request.user
        course_key = CourseKey.from_string(course_id)
        # Course descriptor
        course = get_course_with_access(user, "load", course_key, depth=None, check_if_enrolled=False)
        studio_url = get_studio_url(course, 'settings/grading')

        if not CourseEnrollment.is_enrolled(user, course.id) and \
                not has_access(user, 'staff', course, course.id):
            raise Http404

        # CourseUserGroup object
        user_cohort = get_cohort(user, course_key)
        # cohort_usernames = [user_in.username for user_in in user_cohort.users.all()] if user_cohort else None

        survey_data = script_results_to_visualize(course_key, user_cohort)
        gauge_data = get_script_data(survey_data)
        eda_da = get_eda_da(course_key, user_cohort)

        # eda_da_hardcoded = [['year','sales','expenses'], ['2004', 1000, 400], ['2005', 1000, 400], ['2006', 1000, 400]]

        context = {
            "course": course,
            "staff_access": has_access(user, 'staff', course_key),
            "studio_url": studio_url,
            "survey_json": [json.dumps(x) for x in to_separate_charts(survey_data)],
            "gauge_json": json.dumps(gauge_data),
            "eda_da_json": json.dumps(eda_da),
        }

        return render_to_response("slam/slam.html", context)


def get_eda_da(course_key, user_cohort):
    shortlist_criteria = Q(course_key=course_key) & Q(cohort=user_cohort) & Q(PCI='DA')
    eda_da_sessions = PCI.objects.filter(shortlist_criteria).order_by('session__start')
    if not eda_da_sessions:
        return None
    else:
        eda_da = []
        i = 0
        for eda_da_session in eda_da_sessions:
            i += 1
            try:
                eda_da_session_values = eval(eda_da_session.value)
                eda_da_session_values.insert(0, str(i))
                eda_da.append(eda_da_session_values)
            except NameError:
                # TODO append session number with None values instead of nothing, e.g. [2,None,None,None]
                continue
        column_headers = ['Session', 'Whole group']
        user_cohort.users.all().order_by('email')
        for i in range(0, len(user_cohort.users.all())-1):
            for j in range(i+1, len(user_cohort.users.all())):
                column_headers.append('{} - {}'.format(user_cohort.users.all()[i].username,
                                                     user_cohort.users.all()[j].username))
        eda_da.insert(0, column_headers)

    return eda_da


def get_script_data(survey_data):
    # Script data comes from the surveys and is represented through gauges (gauge_data) and line charts (survey_data)
    # Function to be used together with script_results_to_visualize
    # This function modifies the list passed as argument (survey_data) by inserting the column headers
    # Finnish version v1.1
    gauge_data = [
      ['Label', 'Value'],
      ['Ryhmä', 0],
      ['Tieto', 0],
      ['Tahto', 0],
      ['Tunne', 0]
    ]

    if survey_data:
        if len(survey_data) >= 1:
            column_headers = ['Script', 'Ryhmä', 'Tieto', 'Tahto', 'Tunne']
            survey_data.insert(0, column_headers)
            # TODO number_of_questions here is hardcoded. Better make it a dynamic parameter.
            number_of_questions = 4
            # gauge data
            for question_i in range(1, number_of_questions + 1):
                for i in reversed(range(0, len(survey_data))):
                    if survey_data[i][question_i]:
                        gauge_data[question_i][1] = survey_data[i][question_i]
                        break

    return gauge_data


@login_required
@ensure_valid_course_key
def handle_ajax(request, course_id):
    """
    Handle AJAX for dashboard masquerade: staff users can see the dashboard as the enrolled students they select to.
    """
    dashboard_data = {'success': False}
    course_key = CourseKey.from_string(course_id)
    if request.method == u'GET':
        GET = request.GET
        try:
            # group_id = GET[u'group_id']
            user_name = GET[u'user_name']
        except KeyError:
            # group_id = None
            user_name = None
        if user_name:
            users_in_course = CourseEnrollment.objects.users_enrolled_in(course_key)
            try:
                if '@' in user_name:
                    user = users_in_course.get(email=user_name)
                else:
                    user = users_in_course.get(username=user_name)
            except User.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': _(
                        'There is no user with the username or email address \'{user_name}\' '
                        'enrolled in this course.'
                    ).format(user_name=user_name)
                })
            # CourseUserGroup object
            user_cohort = get_cohort(user, course_key)
            survey_data = script_results_to_visualize(course_key, user_cohort)
            gauge_data = get_script_data(survey_data)
            survey_data = [x for x in to_separate_charts(survey_data)]
            eda_da = get_eda_da(course_key, user_cohort)
            dashboard_data = {'success': True,
                              'survey_data': survey_data,
                              'gauge_data': gauge_data,
                              'eda_da': eda_da,
                              }
            #    json.dumps([survey_data, gauge_data])

    return HttpResponse(json.dumps(dashboard_data), content_type='application/json')


def script_results_to_visualize(course_key, user_cohort):

    try:
        script_results = eval(Script.objects.get(Q(course_key=course_key) & Q(cohort=user_cohort)).results)
    except (NameError, Script.DoesNotExist):
        script_results = None

    return script_results


def to_separate_charts(data_table):

    # Transforms data in ArrayToDataTable format for Google Charts containing N curves in a single chart
    # to an ArrayToDataTable for N charts with a single curve
    single_line_charts = []
    if data_table:
        for i in range(0, len(data_table[0])-1):
            # each question
            single_line_charts.append([])
            # aux_data_table = data_table
            for j in range(0, len(data_table)):
                # each survey
                single_line_charts[i].append([data_table[j][0], data_table[j][i+1]])
    else:
        # TODO putting this manually here is not generalizable
        # The number of empty list should be made dynamically equal to the number of questions in a survey
        single_line_charts = [[], [], [], [], ]

    return single_line_charts
