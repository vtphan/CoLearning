from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
from . import settings
from py4web.utils.form import Form, FormStyleBulma
import datetime

@action('workspace', method='GET')
@action.uses(auth.user, 'workspace.html')
def workspace():
       # if 'student' not in groups.get(auth.get_user()['id']):
       #        redirect(URL('not_authorized'))
       if ('student_id' in request.query) and ('problem_id' in request.query):
              student_id = int(request.query.get('student_id'))
              problem_id = int(request.query.get('problem_id'))
              problem = db.problem[problem_id]
              workspace = db((db.student_workspace.problem_id==problem_id) & (db.student_workspace.student_id==student_id)).select()
              if workspace is None or len(workspace)==0:
                     db.student_workspace.insert(problem_id=problem_id, student_id=student_id, content=problem.problem_description, attempt_left=problem.attempts)
                     db.commit()
                     workspace = db((db.student_workspace.problem_id==problem_id) & (db.student_workspace.student_id==student_id)).select().first()
              else:
                     workspace = workspace.first()
              
              
              url = '%s://%s%s' % (request.environ['wsgi.url_scheme'], request.environ['HTTP_HOST'],
                     request.environ['PATH_INFO'])
              return dict(valid=True, problem=problem, workspace=workspace, current_url=url, time_interval=1000)
       else:
              exit(0)
    
@action('save_workspace', method='POST')
#@action.uses(auth.user, 'workspace.html')
def save_workspace():
       student_id = request.POST['student_id']
       problem_id = request.POST['problem_id']
       content = request.POST['content']
       db((db.student_workspace.problem_id==problem_id)&(db.student_workspace.student_id==student_id)).update(content=content, updated_at=datetime.datetime.now())
       db.commit()

@action('submission_handler', method='POST')
def submission_handler():
       student_id = int(request.POST['student_id'])
       problem_id = int(request.POST['problem_id'])
       content = request.POST['content'].strip()
       attempt_left = int(request.POST['attempt_left'])
       submission_category = int(request.POST['category'])
       submission_id = db.submission.insert(problem_id=problem_id, student_id=student_id, content=content, submission_category=submission_category,\
               submitted_at=datetime.datetime.now())
      
       problem = db.problem[problem_id]
       if submission_category==1:
              if problem.exact_answer==1:
                     if problem.answer == content:
                            verdict, score = "correct", problem.max_points
                            msg = "Your answer for " + problem.problem_name + " is correct."
                     else:
                            verdict, score = "incorrect", 0
                            msg = "Your answer for " + problem.problem_name + " is incorrect!"
                     db.submission_verdict.insert(submission_id=submission_id, verdict=verdict, score=score, evaluated_at=datetime.datetime.now())
                     db((db.student_workspace.problem_id==problem_id)&(db.student_workspace.student_id==student_id)).update(attempt_left=0)
              else:
                     msg = "Your submission for " + problem.problem_name + " will be looked soon."
                     db((db.student_workspace.problem_id==problem_id)&(db.student_workspace.student_id==student_id)).update(attempt_left=attempt_left)
       else:
              msg= "Your help request for "+problem.problem_name+" will be answered soon."
       db.commit()
       return msg