from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
from . import settings
from py4web.utils.form import Form, FormStyleBulma
import datetime

@action('view_workspace/<problem_id>/<student_id>', method='GET')
@action.uses(auth.user, 'workspace_viewer.html')
def view_workspace(problem_id, student_id):
    if 'teacher' not in groups.get(auth.get_user()['id']):
        redirect(URL('not_authorized'))
    # if not (('student_id' in request.query) and ('problem_id' in request.query)):
    #     exit(0)
        
    # student_id = int(request.query.get('student_id'))
    # problem_id = int(request.query.get('problem_id'))
    problem = db.problem[problem_id]
    student = db.auth_user[student_id]
    workspace = db((db.student_workspace.problem_id==problem_id) & (db.student_workspace.student_id==student_id)).select()
    workspace = workspace.first()
    
    
    url = '%s://%s%s' % (request.environ['wsgi.url_scheme'], request.environ['HTTP_HOST'],
            request.environ['PATH_INFO'])
   
    return dict(problem=problem, workspace=workspace, current_url=url, first_name=student.first_name, last_name=student.last_name)