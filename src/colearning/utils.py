from .common import db, groups, auth, flash
from . import settings
import datetime

def create_notification(message, recipients, expire_at, send_editor=False):
    id = db.notification.insert(message=message, recipients=recipients, generated_at=datetime.datetime.now(), expire_at=expire_at)
    for user in recipients:
        db.notification_queue.insert(notification_id=id, user_id=user)
    if send_editor == True:
        for user in recipients:
            db.editor_notification_queue.insert(notification_id=id, user_id=user)
    db.commit()
    

def add_global_value(variable, value):
    db.global_value.update_or_insert(db.global_value.variable==variable, variable=variable, value=value)
    db.commit()
    