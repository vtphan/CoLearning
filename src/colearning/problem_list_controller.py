from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
from . import settings
from py4web.utils.form import Form, FormStyleBulma
import datetime

@action('problem_list', method='GET')
@action.uses(auth.user, 'problem_list.html')
def problem_list():
    if 'teacher' not in groups.get(auth.get_user()['id']):
        redirect(URL('not_authorized'))
    problems = db(db.problem).select(orderby=~db.problem.deadline)
    return dict(problems=problems)
    

