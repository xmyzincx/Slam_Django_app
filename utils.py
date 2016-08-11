# Support functions for the SLAM app
from courseware.models import StudentModule
from django.db.models import Q
from slam.models import Script
from xmodule.mongo_utils import connect_to_mongodb


# Return a list of block_type type descriptors for the course
# List of BlockUsageLocator
# Note: in a cohorted course, this returns all the blocks of type 'block_type'
# although often different cohorts access different resources
def get_blocks_by_type(course_descriptor, block_type="problem"):
    # List for block descriptors
    blocks_in = []
    if course_descriptor is not None:
        for chapter in course_descriptor.get_children():
            if chapter.location.category == block_type:
                blocks_in.append(chapter)
            else:
                for sequential in chapter.get_children():
                    num_surveys_in_seq = 0
                    if sequential.location.category == block_type:
                        blocks_in.append(sequential)
                    else:
                        for vertical in sequential.get_children():
                            if vertical.location.category == block_type:
                                blocks_in.append(vertical)
                            else:
                                for content in vertical.get_children():
                                    if content.location.category == block_type:
                                        blocks_in.append(content)
                    # make sure surveys are in before-after pairs
                    # if num_surveys_in_seq > 2 and num_surveys_in_seq % 2 == 0:
                    #     for i in reversed(range(2, num_surveys_in_seq/2+1)):
                    #         aux = blocks_in.pop(i*-1)
                    #         blocks_in.insert(i*-2+1, aux)

    return blocks_in


def get_mongodb_connection():
    # connect to edX Mongo database
    mongo_database = connect_to_mongodb(
        db='edxapp', host='localhost',
        port=27017, tz_aware=True, user=None,
        password=None, retry_wait_time=0.1
    )

    return mongo_database


def get_survey_fields(structures_collection, block_id):
    # returns a cursor
    survey_document = structures_collection.find(
        {"blocks.block_id": block_id},
        {'blocks': {'$elemMatch': {"block_id": block_id}}}
    ).sort([['edited_on', -1]]).limit(1)
    survey_fields = survey_document[0]["blocks"][0]["fields"]

    return survey_fields


def get_user_survey_answer(course_id, user_id, module_id, questions, answers, question_pos):

    answer_value = None
    shortlist_criteria = Q(student_id=user_id) & Q(module_type='survey') & Q(course_id=course_id)
    user_surveys = StudentModule.objects.filter(shortlist_criteria)
    try:
        # module_state_key is the StudentModule field for the column named module_id
        choices = eval(user_surveys.get(module_state_key=module_id).state)['choices']
    except (NameError, StudentModule.DoesNotExist):
        choices = None
    if choices is not None:
        j = 0
        while j < len(answers) and answers[j][0] != choices[questions[question_pos][0]]:
            j += 1
        answer_value = eval(answers[j][1])

    return answer_value


def save_script_results(course_key, cohort, survey_data):
    # store results for course and cohort in Script table
    kw_script = {
        'course_key': course_key,
        'cohort': cohort,
        'results': survey_data,
    }
    try:
        new_entry = Script.objects.get(course_key=kw_script['course_key'], cohort=kw_script['cohort'])
        new_entry.results = kw_script['results']
    except Script.DoesNotExist:
        new_entry = Script(**kw_script)
    new_entry.save()


def survey_data_to_chart_format(survey_data):
    # Prepare the array in the Google Charts arrayToDataTable format
    survey_data = map(lambda *a: list(a), *survey_data)
    aux_surveydata = []
    for i in range(0, len(survey_data)):
        if survey_data[i].count(None) < len(survey_data[i]):
            # include survey number
            survey_data[i].insert(0, i + 1)
            aux_surveydata.append(survey_data[i])
    survey_data = aux_surveydata

    return survey_data
