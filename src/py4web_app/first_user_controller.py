from py4web import action, request, Field, redirect, URL
from .common import auth, flash
from . import settings
from py4web.utils.form import Form, FormStyleBulma
from pydal.validators import IS_NOT_EMPTY, IS_EMAIL

@action('create_first_user', method=['GET', 'POST'])
@action.uses('create_first_user.html', flash)
def create_first_user():
    if db(db.auth_user).select().first() is not None:
        flash.set('A user already exists.')
        redirect(URL('auth/login'))
    form = Form([
        Field('username', requires=IS_NOT_EMPTY()),
        Field('first_name', requires=IS_NOT_EMPTY()),
        Field('last_name', requires=IS_NOT_EMPTY()),
        Field('email', requires=IS_EMAIL()),
        Field('password', type='password', requires=IS_NOT_EMPTY()),
        ], formstyle=FormStyleBulma)
    if form.accepted:
        user_id = auth.register({
            'email': form.vars.email, 
            'username': form.vars.username, 
            'first_name': form.vars.first_name, 
            'last_name': form.vars.last_name, 
            'password': form.vars.password,
        })
        if user_id.id is None:
            flash.set('Unable to create the first user. ' + '. '.join(user_id.errors.values()))
            redirect(URL('auth/login'))
        else:
            db(db.auth_user.id==user_id.id).update(action_token='')
            groups.add(user_id, ['admin', 'teacher'])
            print(4)
            redirect(URL('auth/login'))
    return dict(form=form)