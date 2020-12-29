from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
from . import settings
from py4web.utils.form import Form, FormStyleBulma
import datetime

from .utils import create_notification

@action('submissions', method='GET')
@action.uses(auth.user, 'submissions.html')
def submissions():
    if 'teacher' not in groups.get(auth.get_user()['id']):
        redirect(URL('not_authorized'))
    active_submissions = db.executesql('SELECT s.id, p.problem_name, st.first_name, st.last_name, s.submission_category, s.submitted_at\
         from submission s, problem p, auth_user st where s.problem_id=p.id and s.student_id=st.id and s.id not in \
             (select submission_id from submission_verdict) and s.id not in (select submission_id from feedback)', as_dict=True)
    return dict(sub=active_submissions)

@action('submission/<submission_id>', method=['GET', 'POST'])
@action.uses(auth.user, 'submission.html')
def submission(submission_id):
    user_id = auth.get_user()['id']
    submission = db.executesql('SELECT s.id, s.content, s.problem_id, p.problem_name, s.student_id, st.first_name, st.last_name, s.submission_category, s.submitted_at\
         from submission s, problem p, auth_user st where s.problem_id=p.id and s.student_id=st.id and s.id='+submission_id, as_dict=True)
    if len(submission)==0 or int(user_id)!=submission[0]['student_id']:
        redirect(URL('not_authorized'))
    
    sub = submission[0]
    help_form = Form([Field('question', type='text')])
    sub['help_form'] = help_form
    
    message = db((db.help_seeking_message.student_id==sub['student_id'])&(db.help_seeking_message.problem_id==sub['problem_id'])&(db.help_seeking_message.submission_id==sub['id'])).select().first()
    sub['message'] = message
    if help_form.accepted:
        message_id = db.help_seeking_message.insert(student_id=user_id, submission_id=sub['id'], problem_id=sub['problem_id'], message=help_form.vars.question,\
            submitted_at=datetime.datetime.now())
        db.help_seeking_message_queue.insert(message_id=message_id)
        db.commit()
        create_notification("New help seeking message recieved.", recipients=[ user['id'] for user in db(db.auth_user).select('id') if 'teacher' in groups.get(user['id'])],\
            expire_at=db.problem[sub['problem_id']].deadline)
    
    return sub

@action('view_submission/<submission_id>', method='GET')
@action.uses(auth.user, 'view_submission.html')
def view_submission(submission_id):
    user_id = auth.get_user()['id']
    submission = db.executesql('SELECT s.id, s.content, s.problem_id, p.problem_name, s.student_id, st.first_name, st.last_name, s.submission_category, s.submitted_at\
         from submission s, problem p, auth_user st where s.problem_id=p.id and s.student_id=st.id and s.id='+submission_id, as_dict=True)
    if len(submission)==0:
        redirect(URL('not_authorized'))
    
    sub = submission[0]
   
    message = db((db.help_seeking_message.student_id==sub['student_id'])&(db.help_seeking_message.problem_id==sub['problem_id'])&(db.help_seeking_message.submission_id==sub['id'])).select().first()
    print(message)
    sub['message'] = message
    return sub

@action('submission_grader', method='GET')
@action.uses(auth.user)
def submission_grader():
    if 'teacher' not in groups.get(auth.get_user()['id']):
        redirect(URL('not_authorized'))
    # print(request.POST.keys())
    # submission_id = int(request.POST['submission_id'])
    # correct = int(request.POST['correct'])
    # feedback = request.POST['feedback']
    submission_id = int(request.query.get('submission_id'))
    correct = int(request.query.get('correct'))
    feedback = request.query.get('feedback')
    # print(submission_id, correct, feedback)
    submission = db.submission[submission_id]
    problem = db.problem[submission.problem_id]
    now = datetime.datetime.now()
    if correct == 1:
        db.submission_verdict.insert(submission_id=submission_id, verdict="correct", score=problem.max_points, evaluated_at=now)
        create_notification("Your answer is correct for problem: "+problem.problem_name, recipients=[submission.student_id], \
            expire_at=datetime.datetime.now()+datetime.timedelta(days=90))
    elif correct == 0:
        credit = float(request.query.get('credit'))
        db.submission_verdict.insert(submission_id=submission_id, verdict="incorrect", score=credit, evaluated_at=now)
        create_notification("Your answer is incorrect for problem: "+problem.problem_name, recipients=[submission.student_id], \
            expire_at=datetime.datetime.now()+datetime.timedelta(days=90))

    if feedback is not None and feedback != "":
        db.feedback.insert(submission_id=submission_id, content=feedback, given_at=now)
    db.commit()
