from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
from . import settings
from py4web.utils.form import Form, FormStyleBulma
import datetime
import math

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
    elif 'student' in groups.get(auth.get_user()['id']):
        user_role = 'student'
    else:
        redirect(URL('not_authorized'))
    if problem_category=='unpublished':
        if user_role == 'student':
            redirect(URL('not_authorized'))
        problems = db(db.problem.deadline==None).select(orderby=~db.problem.problem_uploaded_at)
    elif problem_category=='published':
        problems = db((db.problem.deadline is not None)&(db.problem.deadline>datetime.datetime.utcnow())).select(orderby=~db.problem.deadline)
    elif problem_category=='expired':
        problems = db((db.problem.deadline is not None)&(db.problem.deadline<=datetime.datetime.utcnow())).select(orderby=~db.problem.deadline)
    else:
        problems = None
    return dict(problems=problems, category=problem_category, user_role=user_role, alloted_times = calc_alloted_time(problems))

def calc_alloted_time(problems):
    if problems is None:
        return None
    alloted_times = []
    for p in problems:
        if p.deadline is None:
            alloted_times.append(None)
            continue
        at = p.deadline - p.published_at
        if p.type=='in-class':
            at = int(math.ceil(at.total_seconds()/60))
            if at>1:
                at = str(at)+" minutes"
            else:
                at = str(at)+" minute"
            alloted_times.append(at)
        else:
            alt = str(at.days)+" day"
            if at.days>1:
                alt+= 's'
            hour = int(math.ceil(at.seconds/3600))
            if hour>1:
                alt += " "+str(hour)+" hours"
            elif hour==1:
                alt += " "+str(hour)+" hour"
            alloted_times.append(alt)
    return alloted_times
