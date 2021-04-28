"""
This file defines the database models
"""

from .common import T, db, Field, groups, auth
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
def create_global_parameter(variable, value):
     if db(db.global_value.variable==variable).select().first() is not None:
          return "Variable already exists"
     db.global_value.insert(variable=variable, value=value)
     db.commit()

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
     db.define_table('problem', Field('teacher_id', type='reference auth_user'), Field('problem_name'), Field('problem_description', type='text'), Field('code', type='text'),\
           Field('answer', type='text'), Field('max_points', type='integer'), Field('language'), Field('attempts', type='integer'), Field('problem_uploaded_at', type='datetime'),\
                 Field('exact_answer', type='integer'), Field('deadline', type='datetime'), Field('published_at', type='datetime'), Field('type', requires=IS_IN_SET("in-class", "homework")),\
                       Field('last_updated_at', type='datetime', default=datetime.datetime.utcnow()), redefine=True) 
     db.define_table('problem_topic', Field('problem_id', type='reference problem'), Field('topic_id', type='reference topic'))
     db.define_table('student_workspace', Field('problem_id', type='reference problem'), Field('student_id', type='reference auth_user'), \
          Field('content', type='text'), Field('attempt_left', type='integer'), Field('updated_at', type='datetime', default=datetime.datetime.utcnow()), redefine=True)
     db.define_table('submission', Field('problem_id', type='reference problem'), Field('student_id', type='reference auth_user'),\
          Field('content', type='text'), Field('submitted_at', type='datetime', default=datetime.datetime.utcnow()), \
               Field('submission_category', type='integer', default=1), Field('attempt', type='integer'), redefine=True)
     
     db.define_table('submission_verdict', Field('submission_id', type='reference submission'), Field('verdict'), Field('score', type='double'),\
           Field('evaluated_at', type='datetime'))

     db.define_table('notification', Field('message', type='text'), Field('recipients', type='list:reference auth_user'), Field('generated_at', type='datetime'),\
          Field('expire_at', type='datetime'), Field('type'), Field('type_id', type='integer'), redefine=True)
     db.define_table('global_value', Field('variable'), Field('value'), redefine=True)
     db.define_table('notification_queue', Field('notification_id', type='reference notification'), Field('user_id', type='reference auth_user'))
     db.define_table('editor_notification_queue', Field('notification_id', type='reference notification'), Field('user_id', type='reference auth_user'))
     
     db.define_table('discussion', Field('message', type='text'), Field('code_snapshot', type='text'), Field('student_id', type='reference auth_user'),\
           Field('problem_id', type='reference problem'), Field('author_id', type='reference auth_user'), Field('status', requires=IS_IN_SET(['open', 'closed']), default='open'),\
                 Field('posted_at', type='datetime'))

     db.define_table('comment', Field('message',type='text'), Field('discussion_id', type='reference discussion'), Field('author_id', type='reference auth_user'),\
          Field('posted_at', type='datetime'))
     
     db.define_table('comment_like', Field('comment_id', type='reference comment'), Field('discussion_id', type='reference discussion'), Field('liked_by', type='reference auth_user'),\
           Field('liked_at', type='datetime'), redefine=True)

     db.commit()

create_tables()