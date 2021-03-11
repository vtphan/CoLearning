from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
from . import settings
from py4web.utils.form import Form, FormStyleBulma
import datetime
from pydal.validators import IS_IN_SET, IS_NOT_EMPTY

@action('run_query', method=['GET', 'POST'])
@action.uses(auth.user, 'run_query.html')
def run_query():
    if 'admin' not in groups.get(auth.get_user()['id']):
        redirect(URL('not_authorized'))
    query_form = Form([Field('query', type='text')])
    if query_form.accepted:
        db.executesql(query_form.vars.query)
        db.commit()
    return dict(form=query_form)