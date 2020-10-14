"""
This file defines the database models
"""

from .common import db, Field, groups, auth
from pydal.validators import *

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