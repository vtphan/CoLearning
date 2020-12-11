"""
This file defines the database models
"""

from .common import db, Field, groups, auth
from pydal.validators import *
import datetime
from pydal.validators import IS_IN_SET
### Define your table below
#
# db.define_table('thing', Field('name'))
#
## always commit your models to avoid problems later
#
# db.commit()
#

def create_admin_account(email, username, first_name, last_name, password):
     if db(db.auth_user.email==email).select().first() is not None:
          return "User already exists."
     
     user_id = auth.register({'email': email, 'username': username, 'first_name': first_name, 'last_name': last_name, 'password': password})
     db(db.auth_user.id==user_id).update(action_token='')
     groups.add(user_id, ['admin', 'teacher'])
     db.commit()
     return "Admin added successfully!"

def create_tables():
     db.define_table('topic', Field('topic_description', unique=True))
     db.define_table('problem', Field('teacher_id', type='reference auth_user'), Field('problem_name'), Field('problem_description', type='text'),\
           Field('code', type='text'), Field('answer', type='text'), Field('max_points', type='integer'), Field('language'), Field('attempts', type='integer'), \
                Field('problem_uploaded_at', type='datetime'), Field('exact_answer', type='integer'), Field('deadline', type='datetime'),\
                      Field('last_updated_at', type='datetime', default=datetime.datetime.now()), redefine=True) 
     db.define_table('problem_topic', Field('problem_id', type='reference problem'), Field('topic_id', type='reference topic'))
     db.define_table('student_workspace', Field('problem_id', type='reference problem'), Field('student_id', type='reference auth_user'),\
          Field('content', type='text'), Field('attempt_left', type='integer'), Field('updated_at', type='datetime', default=datetime.datetime.now()), redefine=True)
     db.define_table('submission', Field('problem_id', type='reference problem'), Field('student_id', type='reference auth_user'),\
          Field('content', type='text'), Field('submitted_at', type='datetime', default=datetime.datetime.now()), \
               Field('submission_category', type='integer', default=1), redefine=True)
     
     db.define_table('submission_verdict', Field('submission_id', type='reference submission'), Field('verdict'), Field('score', type='double'),\
           Field('evaluated_at', type='datetime'))
     db.define_table('feedback', Field('submission_id', type='reference submission'), Field('content', type='text'), Field('given_at', type='datetime'))
     db.define_table('alert_message', Field('creator_id', type='reference auth_user'), Field('message', type='text'), Field('problem_id',\
           type='reference problem'), Field('created_at', type='datetime'), redefine=True)
     db.define_table('alert_read', Field('alert_id', type='reference alert_message'), Field('student_id', type='reference auth_user'),\
           Field('read_at', type='datetime'))

     db.define_table('notification', Field('message', type='text'), Field('recipients', type='list:reference auth_user'), Field('generated_at', type='datetime'),\
          Field('expire_at', type='datetime'), redefine=True)
     db.define_table('global_value', Field('variable'), Field('value'), redefine=True)
     db.define_table('notification_queue', Field('notification_id', type='reference notification'), Field('user_id', type='reference auth_user'))

     db.define_table('help_seeking_message', Field('student_id', type='reference auth_user'), Field('problem_id', type='reference problem'), \
          Field('submission_id', type='reference submission'), Field('message', type='text'), Field('submitted_at', type='datetime'))
     db.define_table('help_seeking_message_queue', Field('message_id', type='reference help_seeking_message'))

     db.commit()

create_tables()