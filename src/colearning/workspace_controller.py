from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
from . import settings
from py4web.utils.form import Form, FormStyleBulma
import datetime

from .utils import create_notification

@action('workspace/<student_id>/<problem_id>', method='GET')
@action.uses(auth.user, 'workspace.html')
def workspace(student_id, problem_id):
       if 'student' not in groups.get(auth.get_user()['id']):
              redirect(URL('not_authorized'))
      
       # student_id = int(request.query.get('student_id'))
       # problem_id = int(request.query.get('problem_id'))
       problem = db.problem[problem_id]
       workspace = db((db.student_workspace.problem_id==problem_id) & (db.student_workspace.student_id==student_id)).select()
       if workspace is None or len(workspace)==0:
              db.student_workspace.insert(problem_id=problem_id, student_id=student_id, content=problem.code, attempt_left=problem.attempts)
              db.commit()
              workspace = db((db.student_workspace.problem_id==problem_id) & (db.student_workspace.student_id==student_id)).select().first()
       else:
              workspace = workspace.first()
       
       submissions = db.executesql("select s.id as id, s.content as submission, s.submitted_at, s.submission_category, v.verdict, v.score, f.content as feedback\
               from submission s left join submission_verdict v on s.id=v.submission_id left join feedback f on s.id=f.submission_id where \
                      s.problem_id="+str(problem_id)+" and s.student_id="+str(student_id), as_dict=True)
       url = '%s://%s%s' % (request.environ['wsgi.url_scheme'], request.environ['HTTP_HOST'],
              request.environ['PATH_INFO'])
       # feedbacks = db.executesql("select s.id, s.content, f.content as feedback from feedback f, submission s where f.submission_id==s.id and s.student_id=%d and s.problem_id=%d" % (student_id, problem_id))
       # feedbacks = db((db.feedback.submission_id==db.submission.id)&(db.submission.student_id==student_id)&(db.submission.problem_id==problem_id)).select(db.submission.id, db.submission.content, db.feedback.content)
       # print(datetime.datetime.now(), feedbacks)
       return dict(vproblem=problem, workspace=workspace, current_url=url, time_interval=30000, submissions=submissions, student_name=auth.get_user()['first_name'])
       
    
@action('save_workspace', method='POST')
@action.uses(auth.user)
def save_workspace():
       if not 'student' in groups.get(auth.get_user()['id']):
              redirect(URL('not_authorized'))
       student_id = request.POST['student_id']
       problem_id = request.POST['problem_id']
       content = request.POST['content']
       db((db.student_workspace.problem_id==problem_id)&(db.student_workspace.student_id==student_id)).update(content=content, updated_at=datetime.datetime.now())
       db.commit()

@action('submission_handler', method='POST')
@action.uses(auth.user)
def submission_handler():
       if not 'student' in groups.get(auth.get_user()['id']):
              redirect(URL('not_authorized'))
       student_id = request.json['student_id']
       problem_id = request.json['problem_id']
       content = request.json['content'].strip()
       attempt_left = request.json['attempt_left']
       submission_category = request.json['category']
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
              recipents = [row['id'] for row in db(db.auth_user).select('id') if ('teacher' in groups.get(row['id'])) or ('ta' in groups.get(row['id'])) ]
              create_notification("Help seeking submission recieved.", recipients=recipents, expire_at=problem.deadline)
              msg= "Your help request for "+problem.problem_name+" will be answered soon."

       db.commit()
       return msg