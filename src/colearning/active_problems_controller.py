from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
from . import settings
from py4web.utils.form import Form, FormStyleBulma
import datetime

@action('active_problems', method='GET')
@action.uses(auth.user, 'active_problems.html')
def active_problems():
    # if 'student' not in groups.get(auth.get_user()['id']):
    #     redirect(URL('not_authorized'))
    problems = db(db.problem.deadline>datetime.datetime.utcnow()).select(orderby=~db.problem.problem_uploaded_at)
    return dict(problems=problems)
    

