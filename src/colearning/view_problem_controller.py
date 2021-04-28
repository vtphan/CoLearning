from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
from . import settings
from py4web.utils.form import Form, FormStyleBulma
import datetime
from pydal.validators import IS_IN_SET

from .utils import create_notification, is_eligible_for_help

@action('view_problem/<problem_id>', method='GET')
@action.uses(auth.user, 'view_problem.html')
def view_problem(problem_id):
    user_id = auth.get_user()['id']
    grp = groups.get(user_id)
    student_id = None
    if 'teacher' in grp:
        user_role = 'instructor'
    elif 'ta' in grp:
        user_role = 'ta'
    elif 'student' in grp:
        user_role = 'student'
        student_id = user_id
    else:
        redirect(URL('not_authorized'))
    problem = get_problem_information(problem_id, student_id)
    problem['user_role'] = user_role
    return problem

@action('problem/<problem_id>', method='GET')
@action.uses(auth.user, 'problem.html')
def problem(problem_id):
    problem = get_problem_information(problem_id, auth.get_user()['id'])
    if problem['deadline'] is None:
        redirect(URL('not_authorized'))
    return problem

def get_problem_information(problem_id, student_id=None):
    problem = db.problem[problem_id].as_dict()
    topics = db((db.problem_topic.problem_id==problem_id)&(db.topic.id==db.problem_topic.topic_id)).select(db.topic.topic_description)
    problem['topics'] = ", ".join([row['topic_description'] for row in topics])
    problem['number_of_submission'] = db(db.submission.problem_id==problem_id).count()
    problem['graded_correct'] = db((db.submission.problem_id==problem_id)&(db.submission.id==db.submission_verdict.submission_id)&(db.submission_verdict.verdict=='correct')).count()
    problem['graded_incorrect'] = db((db.submission.problem_id==problem_id)&(db.submission.id==db.submission_verdict.submission_id)&(db.submission_verdict.verdict=='incorrect')).count()
    # problem['teacher_feedback'] = db((db.feedback.problem_id==problem_id)&('teacher' in groups.get(db.feedback.given_by))).count()
    # problem['ta_feedback'] = db((db.feedback.problem_id==problem_id)&('ta' in groups.get(db.feedback.given_by))).count()
    # problem['student_feedback'] = db((db.feedback.problem_id==problem_id)&('student' in groups.get(db.feedback.given_by))).count()
    if student_id is not None:
        problem['student_id'] = student_id
        problem['submissions'] = db((db.submission.student_id==student_id)&(db.submission.problem_id==problem_id)).select(db.submission.id, orderby=~db.submission.submitted_at)
        problem['help_eligible'] = is_eligible_for_help(student_id, problem_id)
    return problem