from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
from . import settings
from py4web.utils.form import Form, FormStyleBulma
import datetime, json

from .utils import create_notification

@action('view_feedback/<feedback_id>', method='GET')
@action.uses(auth.user, 'feedback_view.html')
def view_feedback(feedback_id):
    user_id = auth.get_user()['id']
    feedback = db.feedback[feedback_id]
    # print(feedback.given_for, user_id)
    if feedback.given_for != user_id:
        redirect(URL("not_authorized"))
    problem = db.problem[feedback.problem_id]
    if feedback.help_message_id is not None and feedback.help_message_id!=0:
        message = db.help_queue[feedback.help_message_id].as_dict()
    else:
        message = None
    feedback = feedback.as_dict()
    feedback['language'] = problem.language
    feedback['message'] = message
    return feedback

@action('viewt_feedback/<feedback_id>', method='GET')
@action.uses(auth.user, 'feedbackt_view.html')
def viewt_feedback(feedback_id):
    user_id = auth.get_user()['id']
    if 'teacher' not in groups.get(user_id):
        redirect(URL('not_authorized'))
    feedback = db.feedback[feedback_id]
    problem = db.problem[feedback.problem_id]
    if feedback.help_message_id is not None and feedback.help_message_id!=0:
        message = db.help_queue[feedback.help_message_id].as_dict()
    else:
        message = None
    feedback = feedback.as_dict()
    feedback['language'] = problem.language
    feedback['message'] = message
    return feedback

@action('give_feedback/<sub_or_wp_id>/<type>/<message_id>', method='GET')
@action.uses(auth.user, 'give_feedback.html')
def give_feedback(sub_or_wp_id, type, message_id):
    type = int(type)
    sub_or_wp_id = int(sub_or_wp_id)
    if type == 1: # submission feedback
        sub = db.submission[sub_or_wp_id]
    elif type == 2: # live feedback
        sub = db.student_workspace[sub_or_wp_id]
    else:
        sub = {}
    sub['language'] = db.problem[sub['problem_id']].language
    sub['type'] = type
    # print(dir(sub))
    sub['message_id'] = message_id
    sub['referer'] = request.get_header('Referer')
    return sub.as_dict()

@action('save_feedback', method='GET')
@action.uses(auth.user)
def save_feedback():
    user_id = auth.get_user()['id'] 
    if 'teacher' not in groups.get(user_id):
        redirect(URL('not_authorized'))
    problem_id = int(request.query.get('problem_id'))
    try:
        submission_id = int(request.query.get('submission_id'))
    except Exception as e:
        submission_id = None
    
    code = request.query.get('code')
    feedback = request.query.get('feedback')
    student_id = int(request.query.get('student_id'))
    message_id = int(request.query.get('message_id'))
    feedback_id = db.feedback.insert(problem_id=problem_id, submission_id=submission_id, feedback=feedback, code_snapshot=code,\
         help_message_id=message_id, given_for=student_id, given_by=user_id, given_at=datetime.datetime.utcnow())
    
    if message_id != 0:
        db(db.help_queue.id==message_id).update(status="closed")
    db.commit()

    create_notification("You have got a new feedback. Visit "+URL('view_feedback/'+str(feedback_id), scheme=True), recipients=[student_id],\
        expire_at=db.problem[problem_id].deadline, send_editor=True, type="feedback", type_id=feedback_id)

@action('get_feedback/<feedback_id>', method='GET')
@action.uses(auth.user)
def get_feedback(feedback_id):
    user_id = auth.get_user()['id']
    feedback = db.feedback[feedback_id]
    
    if feedback.given_for != user_id:
        redirect(URL("not_authorized"))
    problem = db.problem[feedback.problem_id]
    feedback = feedback.as_dict()
    feedback['language'] = problem.language
    feedback['problem_name'] = problem.problem_name
    return json.dumps(feedback, default=str)