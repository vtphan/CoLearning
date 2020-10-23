from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
from . import settings
from py4web.utils.form import Form, FormStyleBulma
import datetime

@action('active_problem', method='GET')
@action.uses(auth.user, 'active_problem.html')
def active_problem():
    # if 'student' not in groups.get(auth.get_user()['id']):
    #     redirect(URL('not_authorized'))
    problems = db(db.problem.deadline>datetime.datetime.now()).select()
    return dict(problems=problems)
    

