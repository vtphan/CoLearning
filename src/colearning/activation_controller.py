from py4web import action, request, Field,redirect, URL
from pydal.validators import IS_IN_SET
from .common import db, groups, auth, flash
from . import settings
from py4web.utils.form import Form, FormStyleBulma


@action('activate_user', method=['GET', 'POST'])
@action.uses(auth.user, 'activate_user.html')
def activate_user():
    if not 'admin' in groups.get(auth.get_user()['id']):
        redirect(URL('not_authorized'))

    form = Form([Field('user', requires=IS_IN_SET([user['first_name']+' '+user['last_name']+' ('+user['username']+')'\
         for user in db(db.auth_user.action_token!='').select()])), Field('role', default='Student', requires=IS_IN_SET(['Student', 'Instructor', 'TA', 'Admin', 'Delete']))])
    if form.accepted:
        username = form.vars.user
        username = username[username.rfind('(')+1:-1]
        role = form.vars.role
        user_id = db(db.auth_user.username==username).select('id').first()['id']
        if role == 'Delete':
            db.auth_user(db.auth_user.username==username).update(action_token='account-blocked')
        elif role == 'Student':
            db(db.auth_user.username==username).update(action_token='')
            groups.add(user_id, 'student')
        elif role == 'Instructor':
            db(db.auth_user.id==user_id).update(action_token='')
            groups.add(user_id, 'teacher')
        elif role == 'TA':
            db(db.auth_user.id==user_id).update(action_token='')
            groups.add(user_id, 'ta')
        db.commit()
        if role == "Delete":
            flash.set("User removed successfully!")
        else:
            flash.set("User activated successfully!")
        redirect(URL('problem_list'))
    return dict(form=form)

