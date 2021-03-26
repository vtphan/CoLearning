from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
from . import settings
from py4web.utils.form import Form, FormStyleBulma
import datetime

# @action('problem_list', method='GET')
# @action.uses(auth.user, 'problem_list.html')
# def problem_list():
#     if 'teacher' not in groups.get(auth.get_user()['id']):
#         redirect(URL('not_authorized'))
#     problems = db(db.problem).select(orderby=~db.problem.deadline)
#     return dict(problems=problems)
    

@action('problem_list/<problem_category>')
@action.uses(auth.user, 'problem_list.html')
def problem_list(problem_category='published'):
    if 'teacher' in groups.get(auth.get_user()['id']):
        user_role = 'instructor'
    elif 'ta' in groups.get(auth.get_user()['id']):
        user_role = 'ta'
    else:
        redirect(URL('not_authorized'))
    if problem_category=='unpublished':
        problems = db(db.problem.deadline==None).select(orderby=~db.problem.problem_uploaded_at)
    elif problem_category=='published':
        problems = db((db.problem.deadline is not None)&(db.problem.deadline>datetime.datetime.utcnow())).select(orderby=~db.problem.deadline)
    elif problem_category=='expired':
        problems = db((db.problem.deadline is not None)&(db.problem.deadline<=datetime.datetime.utcnow())).select(orderby=~db.problem.deadline)
    else:
        problems = None
    return dict(problems=problems, category=problem_category, user_role=user_role)