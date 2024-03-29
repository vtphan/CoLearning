from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth
from py4web.utils.form import Form, FormStyleBulma
import datetime
import json
from .utils import create_notification, is_eligible_for_help

#-------------------------------------------------------------------
# todo: fix this
#-------------------------------------------------------------------

@action('discussion/<student_id>/<problem_id>/<discussion_id>', method='GET')
@action.uses(auth.user, 'discussion_view.html')
def discussion_view(student_id, problem_id, discussion_id):
    user_id = auth.get_user()['id']
    grp = groups.get(user_id)
    if 'teacher' in grp:
        user_role = 'teacher'
    elif 'ta' in grp:
        user_role = 'ta'
    elif 'student' in grp:
        user_role = 'student'
        if not(int(student_id) == user_id or is_eligible_for_help(user_id, problem_id)):
	        redirect(URL('not_authorized'))
    else:
        redirect(URL('not_authorized'))

    return dict(user_role=user_role)

#-------------------------------------------------------------------
@action('students_view_discussions', method='GET')
@action.uses(auth.user, 'students_view_discussions.html')
def students_view_discussions():
    user_id = auth.get_user()['id']
    if 'student' not in groups.get(user_id):
        redirect(URL('not_authorized'))
    query = (db.is_tutor.student_id==user_id) & (db.is_tutor.problem_id==db.discussion.problem_id)
    rows = db(query).select(orderby=~db.discussion.posted_at)
    return dict(rows=rows)

#-------------------------------------------------------------------
@action('my_discussions', method='GET')
@action.uses(auth.user, 'my_discussions.html')
def my_discussions():
    user_id = auth.get_user()['id']
    if 'student' not in groups.get(user_id):
        redirect(URL('not_authorized'))
    query = (db.discussion.student_id==user_id) | (db.discussion.author_id==user_id)
    rows = db(query).select(orderby=~db.discussion.posted_at)
    return dict(rows=rows)

#-------------------------------------------------------------------
@action('teachers_view_discussions', method='GET')
@action.uses(auth.user, 'teachers_view_discussions.html')
def teachers_view_discussions():
    user_id = auth.get_user()['id']
    if 'teacher' not in groups.get(user_id) and 'ta' not in groups.get(user_id):
        redirect(URL('not_authorized'))
    rows = db(db.discussion.id>0).select(orderby=~db.discussion.posted_at)
    return dict(rows=rows, user_role='teacher')

#-------------------------------------------------------------------

