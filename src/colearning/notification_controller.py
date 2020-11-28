from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
import datetime
import json
from pydal.validators import IS_IN_SET

@action('get_notification/<user_id>', method='GET')
@action.uses(auth.user)
def get_notification(user_id):
    notifs = db((db.notification_queue.user_id==user_id)&(db.notification_queue.notification_id==db.notification.id)\
        &(db.notification.expire_at>=datetime.datetime.now())).select().as_list()
    db(db.notification_queue.user_id==user_id).delete()
    db.commit()
    
    return json.dumps(notifs, default=str)