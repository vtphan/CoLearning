from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
import datetime
from pydal.validators import IS_IN_SET
from py4web.utils.form import Form, FormStyleBulma

@action('global_values', method=['GET', 'POST'])
@action.uses(auth.user, 'global_values.html')
def global_values():
    if 'teacher' not in groups.get(auth.get_user()['id']):
        redirect(URL('not_authorized'))
        
    gv = db(db.global_value).select()
    form = Form([Field(row['variable'], default=row['value']) for row in gv], formstyle=FormStyleBulma, form_name='global_values', keep_values=True)
    if form.accepted:
        for row in gv:
            db(db.global_value.variable==row['variable']).update(value=form.vars[row['variable']])
        db.commit()

    return dict(form=form)