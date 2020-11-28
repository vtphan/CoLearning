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
    
@action('view_submission', method='GET')
@action.uses(auth.user, 'view_submission.html')
def view_submission():
    if 'teacher' not in groups.get(auth.get_user()['id']):
        redirect(URL('not_authorized'))
    
    if 'submission_id' not in request.query:
        return "<script>alert('Invalid query!');</script>"
        redirect(URL('submissions'))

    submission_id = request.query.get('submission_id')
    submission = db.executesql('SELECT s.id, s.content, p.problem_name, st.first_name, st.last_name, s.submission_category, s.submitted_at\
         from submission s, problem p, auth_user st where s.problem_id=p.id and s.student_id=st.id and s.id='+submission_id, as_dict=True)
    
    return submission[0]

@action('submission_grader', method='POST')
@action.uses(auth.user)
def submission_grader():
    if 'teacher' not in groups.get(auth.get_user()['id']):
        redirect(URL('not_authorized'))

    submission_id = int(request.POST['submission_id'])
    correct = int(request.POST['correct'])
    feedback = request.POST['feedback']
    submission = db.submission[submission_id]
    problem = db.problem[submission.problem_id]
    now = datetime.datetime.now()
    if correct == 1:
        db.submission_verdict.insert(submission_id=submission_id, verdict="correct", score=problem.max_points, evaluated_at=now)
        create_notification("Your answer is correct for problem: "+problem.problem_name, recipients=[submission.student_id], \
            expire_at=datetime.datetime.now()+datetime.timedelta(months=3))
    elif correct == 0:
        credit = float(request.POST['credit'])
        db.submission_verdict.insert(submission_id=submission_id, verdict="incorrect", score=credit, evaluated_at=now)
        create_notification("Your answer is incorrect for problem: "+problem.problem_name, recipients=[submission.student_id], \
            expire_at=datetime.datetime.now()+datetime.timedelta(months=3))

    if feedback is not None and feedback != "":
        db.feedback.insert(submission_id=submission_id, content=feedback, given_at=now)
    db.commit()
