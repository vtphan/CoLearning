from re import sub
from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
from . import settings
from py4web.utils.form import Form, FormStyleBulma
import datetime

from .utils import create_notification, is_eligible_for_help

@action('submissions', method='GET')
@action.uses(auth.user, 'submissions.html')
def submissions():
    if 'teacher' in groups.get(auth.get_user()['id']):
        user_role = 'teacher'
    elif 'ta' in groups.get(auth.get_user()['id']):
        user_role = 'ta'
    elif 'student' in groups.get(auth.get_user()['id']):
        user_role = 'student'
    else:
        redirect(URL('not_authorized'))

    category = 'ungraded'
    if 'type' in request.query:
        category = request.query.get('type')

    if category=='ungraded':
        q = (db.submission_verdict.submission_id==None)
        q &= (db.submission.problem_id == db.problem.id)
        q &= (db.submission.student_id == db.auth_user.id)
        if user_role=='student':
            q &= (db.submission.student_id == auth.get_user()['id'])
        subs = db(q).select(
            db.submission.id, db.submission.submitted_at, 
            db.problem.id, db.problem.problem_name, 
            db.auth_user.first_name, db.auth_user.last_name,
            orderby = ~db.submission.submitted_at,
            left = db.submission_verdict.on(db.submission.id == db.submission_verdict.submission_id))
    else:
        q = (db.submission.id == db.submission_verdict.submission_id)
        q &= (db.submission.problem_id == db.problem.id)
        q &= (db.submission.student_id == db.auth_user.id)
        if user_role=='student':
            q &= (db.submission.student_id == auth.get_user()['id'])
        subs = db(q).select(
            db.submission.id, db.submission.submitted_at, 
            db.problem.id, db.problem.problem_name, 
            db.auth_user.first_name, db.auth_user.last_name,
            orderby = ~db.submission.submitted_at,
            )


    return dict(subs=subs, user_role=user_role, category=category)

#-----------------------------------------------------------------------------
# 5.5.2021 -- TO BE REMOVED
#-----------------------------------------------------------------------------

# @action('my_submissions', method='GET')
# @action.uses(auth.user, 'my_submissions.html')
# def my_submissions():
#     user_id = auth.get_user()['id']
#     if 'student' not in groups.get(user_id):
#         redirect(URL('not_authorized'))
#     submissions = db.executesql('SELECT s.id, s.problem_id, p.problem_name, s.submitted_at\
#          from submission s, problem p where s.problem_id=p.id order by s.submitted_at desc', as_dict=True)
#     return dict(sub=submissions, user_role='student')

#-----------------------------------------------------------------------------

# @action('submission/<submission_id>', method=['GET', 'POST'])
# @action.uses(auth.user, 'submission.html')
# def submission(submission_id):
#     user_id = auth.get_user()['id']
#     submission = db.executesql('SELECT s.id, s.content, s.problem_id, p.problem_name, p.language, s.student_id, st.first_name, st.last_name, s.submission_category, s.submitted_at\
#          from submission s, problem p, auth_user st where s.problem_id=p.id and s.student_id=st.id and s.id='+submission_id, as_dict=True)
#     if len(submission)==0 or int(user_id)!=submission[0]['student_id']:
#         redirect(URL('not_authorized'))
    
#     sub = submission[0]
#     help_form = Form([Field('message', label="Explain the problem you are facing")])
#     sub['help_form'] = help_form
#     verdict = db(db.submission_verdict.submission_id==submission_id).select()
#     sub['verdict'] = verdict
#     submissions = db((db.submission.student_id==sub['student_id'])&(db.submission.problem_id==sub['problem_id'])).select(db.submission.id, orderby=~db.submission.submitted_at)
#     sub['submissions'] = submissions
#     if help_form.accepted:
        
#         db.help_queue.insert(student_id=user_id, problem_id=sub['problem_id'], submission_id=sub['id'], message=help_form.vars.message, asked_at=datetime.datetime.utcnow())
#         db.commit()
#         create_notification("New help seeking message recieved.", recipients=[ user['id'] for user in db(db.auth_user).select('id') if 'teacher' in groups.get(user['id'])],\
#             expire_at=db.problem[sub['problem_id']].deadline)
#     sub['user_role'] = 'student'
#     return sub

#-----------------------------------------------------------------------------
# queries can be simplified here.
#-----------------------------------------------------------------------------

@action('view_submission/<submission_id>', method='GET')
@action.uses(auth.user, 'view_submission.html')
def view_submission(submission_id):
    if 'teacher' in groups.get(auth.get_user()['id']):
        user_role = 'teacher'
    elif 'ta' in groups.get(auth.get_user()['id']):
        user_role = 'ta'
    elif 'student' in groups.get(auth.get_user()['id']):
        user_role = 'student'
    else:
        redirect(URL('not_authorized'))
    user_id = auth.get_user()['id']
    submission = db.executesql('SELECT s.id, s.content, s.problem_id, p.problem_name, p.language, s.student_id, st.first_name, st.last_name, s.submission_category, s.submitted_at\
         from submission s, problem p, auth_user st where s.problem_id=p.id and s.student_id=st.id and s.id='+submission_id, as_dict=True)
    if len(submission)==0:
        redirect(URL('not_authorized'))
    
    sub = submission[0]
    sub['help_eligible'] = user_id==sub['student_id'] or is_eligible_for_help(user_id, sub['problem_id'])
    if not sub['help_eligible']:
        redirect(URL('not_authorized'))
        
    q = (db.submission.student_id==sub['student_id']) & (db.submission.problem_id==sub['problem_id'])
    submissions = db(q).select(db.submission.id, orderby=~db.submission.submitted_at)
    verdict = db(db.submission_verdict.submission_id==submission_id).select()
    sub['verdict'] = verdict
    ref = request.get_header('Referer')
    if ref is not None:
        ref = ref.split('/')
    help_message_id = 0
    if ref is not None and len(ref)>2 and ref[-2]=='view_help_message':
            help_message_id = int(ref[-1])
            if db.help_queue[help_message_id].status == "opened":
                db(db.help_queue.id==help_message_id).update(status='viewed')
                db.commit()
    sub['help_message_id'] = help_message_id
    sub['referer'] = request.get_header('Referer')
    sub['submissions'] = submissions
    sub['user_role'] = user_role
    return sub

#-----------------------------------------------------------------------------
@action('submission_grader', method='GET')
@action.uses(auth.user)
def submission_grader():
    if 'teacher' not in groups.get(auth.get_user()['id']) and 'ta' not in groups.get(auth.get_user()['id']):
        redirect(URL('not_authorized'))
    submission_id = int(request.query.get('submission_id'))
    correct = int(request.query.get('correct'))
    submission = db.submission[submission_id]
    problem = db.problem[submission.problem_id]

    now = datetime.datetime.utcnow()
    if correct == 1:
        db.submission_verdict.update_or_insert(db.submission_verdict.submission_id==submission_id, submission_id=submission_id, verdict="correct", score=problem.max_points, evaluated_at=now)
        db((db.student_workspace.problem_id==problem.id)&(db.student_workspace.student_id==submission.student_id)).update(attempt_left=0)
        create_notification("Your "+ get_number_word(submission.attempt)+" submission for problem: "+problem.problem_name+" is correct.", recipients=[submission.student_id], \
            expire_at=datetime.datetime.utcnow()+datetime.timedelta(days=90), send_editor=True)
        db.is_tutor.insert(problem_id=submission.problem_id, student_id=submission.student_id)
    elif correct == 0:
        credit = float(request.query.get('credit'))
        db.submission_verdict.update_or_insert(db.submission_verdict.submission_id==submission_id, submission_id=submission_id, verdict="incorrect", score=credit, evaluated_at=now)
        create_notification("Your "+ get_number_word(submission.attempt) +" submission for problem: "+problem.problem_name+" is incorrect.", recipients=[submission.student_id], \
            expire_at=datetime.datetime.utcnow()+datetime.timedelta(days=90), send_editor=True)

    db.commit()

#-----------------------------------------------------------------------------

def get_number_word(n):
    if n==1:
        return 'first'
    if n==2:
        return 'second'
    if n==3:
        return 'third'
    if n==11:
        return '11th'
    if n==12:
        return '12th'
    if n%10==1:
        return str(n)+'st'
    if n%10==2:
        return str(n)+'nd'
    if n%10==3:
        return str(n)+'rd'
    return str(n)+'th'