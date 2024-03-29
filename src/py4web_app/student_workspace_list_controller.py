from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
from . import settings
from py4web.utils.form import Form, FormStyleBulma
import datetime

@action('student_workspace_list/<problem_id>', method='GET')
@action.uses(auth.user, 'student_workspace_list.html')
def problem_list(problem_id):
    if 'teacher' in groups.get(auth.get_user()['id']):
        user_role = 'instructor'
    elif 'ta' in groups.get(auth.get_user()['id']):
        user_role = 'ta'
    elif 'student' in groups.get(auth.get_user()['id']):
        user_role = 'student'    
    else:
        redirect(URL('not_authorized'))
    student_list = db.executesql('select w.student_id, a.first_name, a.last_name from student_workspace w, auth_user\
         a where w.problem_id='+problem_id+' and a.id=w.student_id', as_dict=True)
    
    discussion_list = db(db.discussion.student_id==db.discussion.author_id).select()

    discussions = dict()
    for d in discussion_list:
        discussions[(d.student_id, d.problem_id)] = True
    
    return dict(students=student_list, problem_id=problem_id, user_role=user_role, discussions=discussions)
    

