from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
from . import settings
from py4web.utils.form import Form, FormStyleBulma
import datetime

@action('student_workspace_list/<problem_id>', method='GET')
@action.uses(auth.user, 'student_workspace_list.html')
def problem_list(problem_id):
    if 'teacher' not in groups.get(auth.get_user()['id']):
        redirect(URL('not_authorized'))
    student_list = db.executesql('select w.student_id, a.first_name, a.last_name from student_workspace w, auth_user\
         a where w.problem_id='+problem_id+' and a.id=w.student_id', as_dict=True)
    
    return dict(students=student_list, problem_id=problem_id)
    

