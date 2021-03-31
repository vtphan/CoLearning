from .common import db, groups, auth, flash
from . import settings
import datetime

def create_notification(message, recipients, expire_at, send_editor=False, type=None, type_id=0):
    id = db.notification.insert(message=message, recipients=recipients, type=type, type_id=type_id,\
         generated_at=datetime.datetime.utcnow(), expire_at=expire_at)
    for user in recipients:
        db.notification_queue.insert(notification_id=id, user_id=user)
    if send_editor == True:
        for user in recipients:
            db.editor_notification_queue.insert(notification_id=id, user_id=user)
    db.commit()
    

def add_global_value(variable, value):
    db.global_value.update_or_insert(db.global_value.variable==variable, variable=variable, value=value)
    db.commit()
    
def is_eligible_for_help(user_id, problem_id):
    if ('teacher' or 'ta') in groups.get(user_id):
        return True
    if 'student' in groups.get(user_id):
        if len(db((db.submission.problem_id==problem_id)&(db.submission.student_id==user_id)& \
            (db.submission_verdict.submission_id==db.submission.id)&(db.submission_verdict.verdict=='correct')).select())>0:
            return True
    return False