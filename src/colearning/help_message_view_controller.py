from os import setuid
from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
from . import settings
from py4web.utils.form import Form, FormStyleBulma
import datetime

from .utils import create_notification

@action('student_help_message_list', method='GET')
@action.uses(auth.user, 'student_help_message_list.html')
def student_help_message_list():
    user_id = auth.get_user()['id']
    if ('teacher' or 'ta') in groups.get(user_id):
        messages = db.executesql("select s.first_name, s.last_name, h.id as message_id, h.student_id, h.problem_id, p.problem_name, h.message, h.status \
            from help_queue h, problem p, auth_user s where p.id=h.problem_id and s.id=h.student_id and h.status<>\"closed\" order by h.asked_at desc", as_dict=True)

        past_messages = db.executesql("select s.first_name, s.last_name, h.id as message_id, h.student_id, h.problem_id, p.problem_name, h.message, h.status\
            from help_queue h, problem p, auth_user s where p.id=h.problem_id and s.id=h.student_id and h.status=\"closed\" order by h.asked_at desc", as_dict=True)
    elif 'student' in groups.get(user_id):
        messages = db.executesql("select s.first_name, s.last_name, h.id as message_id, h.student_id, h.problem_id, p.problem_name, h.message, h.status \
            from help_queue h, problem p, auth_user s where p.id=h.problem_id and s.id=h.student_id and h.status<>\"closed\" and \
                p.id in (select problem_id from submission sb, submission_verdict sv where sb.id=sv.submission_id and sb.student_id="+str(user_id)+") order by h.asked_at desc", as_dict=True)
        past_messages = []

    return dict(messages=messages, past_messages=past_messages)

@action('help_message_list', method='GET')
@action.uses(auth.user, 'help_message_list.html')
def help_message_list():
    user_id = auth.get_user()['id']
    if 'teacher' in groups.get(user_id):
        user_role = 'instructor'
    elif 'ta' in groups.get(user_id):
        user_role = 'ta'
    else:
        redirect(URL('not_authorized'))
    
    messages = db.executesql("select s.first_name, s.last_name, h.id as message_id, h.student_id, h.problem_id, p.problem_name, h.message, h.status \
        from help_queue h, problem p, auth_user s where p.id=h.problem_id and s.id=h.student_id and h.status<>\"closed\" order by h.asked_at desc", as_dict=True)

    past_messages = db.executesql("select s.first_name, s.last_name, h.id as message_id, h.student_id, h.problem_id, p.problem_name, h.message, h.status\
        from help_queue h, problem p, auth_user s where p.id=h.problem_id and s.id=h.student_id and h.status=\"closed\" order by h.asked_at desc", as_dict=True)

    return dict(messages=messages, past_messages=past_messages, user_role=user_role)

@action('view_help_message/<message_id>', method=['GET', 'POST'])
@action.uses(auth.user, 'view_help_message.html')
def view_help_message(message_id):
    if 'teacher' in groups.get(auth.get_user()['id']):
        user_role = 'instructor'
    elif 'ta' in groups.get(auth.get_user()['id']):
        user_role = 'ta'
    else:
        redirect(URL('not_authorized'))

    message = db.help_queue[message_id]
    problem = db.problem[message.problem_id]
    student = db.auth_user[message.student_id]

    if db.help_queue[message_id].status == "not opened":
        db(db.help_queue.id==message_id).update(status='opened')
        db.commit()
    if message.submission_id is None:
        submission = None
        code_snapshot = db((db.student_workspace.problem_id==message.problem_id)&(db.student_workspace.student_id==message.student_id)).select().first().content
    else:
        submission = db.submission[message.submission_id]
        code_snapshot = submission.content
    feedback = db(db.feedback.help_message_id==message_id).select().first()
    if feedback is not None:
        feedback = feedback.feedback
    else:
        feedback = ""

    return dict(message=message, submission=submission, problem=problem, student_name=student.first_name+" "+student.last_name, code_snapshot=code_snapshot, feedback=feedback, user_role=user_role)

@action('help_message/<message_id>', method=['GET', 'POST'])
@action.uses(auth.user, 'help_message.html')
def view_help_message(message_id):
    message = db.help_queue[message_id]
    problem = db.problem[message.problem_id]
    student = db.auth_user[message.student_id]
    if not is_eligible_for_help(auth.get_user()['id'], problem.id):
        redirect(URL('not_authorized'))
    if db.help_queue[message_id].status == "not opened":
        db(db.help_queue.id==message_id).update(status='opened')
        db.commit()
    if message.submission_id is None:
        submission = None
        code_snapshot = db((db.student_workspace.problem_id==message.problem_id)&(db.student_workspace.student_id==message.student_id)).select().first().content
    else:
        submission = db.submission[message.submission_id]
        code_snapshot = submission.content
    feedback = db(db.feedback.help_message_id==message_id).select().first()
    if feedback is not None:
        feedback = feedback.feedback
    else:
        feedback = ""

    return dict(message=message, submission=submission, problem=problem, student_name=student.first_name+" "+student.last_name, code_snapshot=code_snapshot, feedback=feedback)

def is_eligible_for_help(user_id, problem_id):
    if ('teacher' or 'ta') in groups.get(user_id):
        return True
    if 'student' in groups.get(user_id):
        if len(db((db.submission.problem_id==problem_id)&(db.submission.student_id==user_id)& \
            (db.submission_verdict.submission_id==db.submission.id)&(db.submission_verdict.verdict=='correct')).select())>0:
            return True
    return False
