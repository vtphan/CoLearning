from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
from . import settings
from py4web.utils.form import Form, FormStyleBulma
import datetime

from .utils import create_notification

@action('help_message_list', method='GET')
@action.uses(auth.user, 'help_message_list.html')
def help_message_list():
    messages = db.executesql("select s.first_name, s.last_name, h.id as message_id, h.student_id, h.problem_id, p.problem_name, h.message, h.status \
        from help_queue h, problem p, auth_user s where p.id=h.problem_id and s.id=h.student_id and h.status<>\"closed\" order by h.asked_at desc", as_dict=True)

    past_messages = db.executesql("select s.first_name, s.last_name, h.id as message_id, h.student_id, h.problem_id, p.problem_name, h.message, h.status\
        from help_queue h, problem p, auth_user s where p.id=h.problem_id and s.id=h.student_id and h.status=\"closed\" order by h.asked_at desc", as_dict=True)
    
    return dict(messages=messages, past_messages=past_messages)

@action('view_help_message/<message_id>', method=['GET', 'POST'])
@action.uses(auth.user, 'view_help_message.html')
def view_help_message(message_id):
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

    return dict(message=message, submission=submission, problem=problem, student_name=student.first_name+" "+student.last_name, code_snapshot=code_snapshot, feedback=feedback)