from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
from . import settings
from py4web.utils.form import Form, FormStyleBulma
import datetime
from pydal.validators import IS_IN_SET, IS_NOT_EMPTY, IS_INT_IN_RANGE

from .utils import create_notification, add_global_value

@action('new_problem', method=['GET', 'POST'])
@action.uses(auth.user, 'new_problem.html', flash)
def new_inclass_problem():
    grp = groups.get(auth.get_user()['id'])
    if not ('teacher' in grp or 'ta' in grp) :
        redirect(URL('not_authorized'))
    default_lang = db(db.global_value.variable=='language').select()
    if len(default_lang) == 0:
        default_lang = "Python"
    else:
        default_lang = default_lang.first()['value']
    problem_form = Form(
        [
            Field('problem_name', requires=IS_NOT_EMPTY(), default='assignment_'+datetime.datetime.utcnow().strftime("%Y%m%d%M%S")),
            Field('number_of_attempts', requires=IS_INT_IN_RANGE(1,11), default=1),
            Field('maximum_score', requires=IS_INT_IN_RANGE(1,101), default=10),
            Field('problem_description', 'text', requires=IS_NOT_EMPTY()),
            Field('helper_code', 'text'),
            Field('language', requires=IS_IN_SET(['Python', 'Java', 'C++']), default=default_lang),
            Field('problem_type', requires=IS_IN_SET(['in-class','homework']), default='in-class'),
            Field('answer'),
            Field('topics'),
        ], 
        formstyle=FormStyleBulma
    )
    if problem_form.accepted:
        if problem_form.vars.answer.strip() != "":
            exact_answer = 1
        else:
            exact_answer = 0
        teacher_id = auth.get_user()['id']
        
        pid = db.problem.insert(
            teacher_id=teacher_id, 
            problem_description=problem_form.vars.problem_description, 
            code=problem_form.vars.helper_code,
            answer=problem_form.vars.answer.strip(), 
            problem_name=problem_form.vars.problem_name.strip(), 
            max_points=problem_form.vars.maximum_score,
            attempts=problem_form.vars.number_of_attempts, 
            language=problem_form.vars.language,
            problem_uploaded_at=datetime.datetime.utcnow(),
            last_updated_at=datetime.datetime.utcnow(),
            exact_answer=exact_answer, 
            type=problem_form.vars.problem_type)
        deadline=None

        topics = problem_form.vars.topics.strip()
        if topics != "":
            for topic in topics.split(','):
                tmp = db(db.topic.topic_description==topic).select()
                if len(tmp)==0:
                    topic_id = db.topic.insert(topic_description=topic)
                else:
                    topic_id = tmp.first()['id']
                db.problem_topic.insert(problem_id=pid, topic_id=topic_id)
        db.commit()
        add_global_value('language', problem_form.vars.language)
        flash.set(message='Problem '+problem_form.vars.problem_name.strip()+' has been added successfully.')
        if deadline is not None:
            users = [row['id'] for row in db(db.auth_user).select('id') if row['id']!=teacher_id]
            create_notification('New in-class exercise '+problem_form.vars.problem_name+' has been added.', users, deadline)
        redirect(URL('view_problem/'+str(pid)))

    return dict(form=problem_form, user_role='instructor')

