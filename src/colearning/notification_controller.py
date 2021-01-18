from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
import datetime
import json
from pydal.validators import IS_IN_SET

@action('get_notification', method='GET')
@action.uses(auth.user)
def get_notification():
    user_id = auth.get_user()['id']
    notifs = db((db.notification_queue.user_id==user_id)&(db.notification_queue.notification_id==db.notification.id)\
        &(db.notification.expire_at>=datetime.datetime.now())).select().as_list()
    db(db.notification_queue.user_id==user_id).delete()
    db.commit()
    
    return json.dumps(notifs, default=str)

@action('get_editor_notification', method='GET')
@action.uses(auth.user)
def get_editor_notification():
    user_id = auth.get_user()['id']
    
    notif_message = ""
    notifs = db((db.editor_notification_queue.user_id==user_id)&(db.editor_notification_queue.notification_id==db.notification.id)\
        &(db.notification.expire_at>=datetime.datetime.now())).select(orderby=db.notification.generated_at, limitby=(0, 1))
    if len(notifs) == 1:
        notif_message = notifs.first()['notification.message']
        db(db.editor_notification_queue.id==notifs.first()['notification.id']).delete()
    expired_entries = db(db.notification.expire_at>=datetime.datetime.now()).select(db.notification.id)
    db(db.editor_notification_queue.notification_id.belongs([row['id'] for row in expired_entries])).delete()
    db.commit()
    return notif_message

