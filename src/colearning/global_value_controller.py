from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
import datetime
from pydal.validators import IS_IN_SET
from py4web.utils.form import Form, FormStyleBulma

@action('global_values', method='GET')
@action.uses(auth.user, 'global_value.html')
def global_values():
    gv = db(db.global_value).select()
    form = Form([Field('variable_name', requires=IS_IN_SET([row['variable'] for row in gv]), _test='test'), Field('value')], formstyle=FormStyleBulma, form_name='global_values', keep_values=True)
    
    return dict(form=form)