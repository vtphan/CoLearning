from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
from . import settings
from py4web.utils.form import Form, FormStyleBulma
import datetime

@action('workspace', method='GET')
@action.uses(auth.user, 'workspace.html')
def workspace():
    # if 'student' not in groups.get(auth.get_user()['id']):
    #     redirect(URL('not_authorized'))
    problems = db(db.problem.deadline>datetime.datetime.now()).select()
    # print(request.environ)
    url = '%s://%s%s' % (request.environ['wsgi.url_scheme'], request.environ['HTTP_HOST'],
           request.environ['PATH_INFO'])
    return dict(problems=problems, current_url=url)
    

