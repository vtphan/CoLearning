from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
from . import settings
from py4web.utils.form import Form, FormStyleBulma
import datetime

from .utils import create_notification

@action('help_message_list', method='GET')
@action.uses(auth.user, 'help_message_list.html')
def help_message_list():
    messages = db.executesql("select s.first_name, s.last_name, h.id as message_id, h.student_id, h.problem_id, p.problem_name, h.message\
        from help_seeking_message h, problem p, auth_user s where p.id=h.problem_id and s.id=h.student_id and h.reply is NULL", as_dict=True)

    past_messages = db.executesql("select s.first_name, s.last_name, h.id as message_id, h.student_id, h.problem_id, p.problem_name, h.message\
        from help_seeking_message h, problem p, auth_user s where p.id=h.problem_id and s.id=h.student_id and h.reply is not NULL", as_dict=True)
    
    return dict(messages=messages, past_messages=past_messages)

@action('view_help_message/<message_id>', method=['GET', 'POST'])
@action.uses(auth.user, 'view_help_message.html')
def view_help_message(message_id):
    message = db.help_seeking_message[message_id]
    problem = db.problem[message.problem_id]
    if message.submission_id is not None:
        submission = db.submission[message.submission_id]
    else:
        submission = None
    # workspace = db((db.student_workspace.student_id==message.student_id) & (db.student_workspace.problem_id==message.problem_id)).select()
    student = db.auth_user[message.student_id]
    # have to delete from queue
    reply_form = Form([Field('reply', type='text')])
    if reply_form.accepted:
        db.help_seeking_message[message_id] = dict(reply=reply_form.vars.reply, replied_at=datetime.datetime.now())
        db.commit()
        create_notification("Recieved reply from instructor/TA.", recipients=[message.student_id],expire_at=problem.deadline)


    return dict(message=message, submission=submission, problem=problem, student_name=student.first_name+" "+student.last_name, reply_form=reply_form)