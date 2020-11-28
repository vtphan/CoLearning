from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
from . import settings
from py4web.utils.form import Form, FormStyleBulma
import datetime
from pydal.validators import IS_IN_SET

from .utils import create_notification, add_global_value

@action('new_problem', method=['GET', 'POST'])
@action.uses(auth.user, 'new_problem.html', flash)
def new_problem():
    if not 'teacher' in groups.get(auth.get_user()['id']):
        redirect(URL('not_authorized'))
    default_lang = db(db.global_value.variable=='language').select()
    if len(default_lang) == 0:
        default_lang = "Python"
    else:
        default_lang = default_lang.first()['value']
    default_deadline = (datetime.datetime.now()+datetime.timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    problem_form = Form(
        [
            Field('problem_name', required=True, default='assignment_'+datetime.datetime.now().strftime("%Y%m%d%M%S")),
            Field('deadline', "datetime", default=default_deadline.strftime('%Y-%m-%d %H:%M')),
            Field('number_of_attempts', type='integer', default=1),
            Field('maximum_score', type='integer', default=10),
            Field('problem_description', 'text'),
            Field('language', requires=IS_IN_SET(['Python', 'Java', 'C++']), default=default_lang),
            Field('content', 'text'),
            Field('answer'),
            Field('topics'),
        ], 
        formstyle=FormStyleBulma
    )
    if problem_form.accepted:
        if problem_form.vars.content == "":
            flash.set(message='Problem description can not be empty.')
        elif problem_form.vars.problem_name == "":
            flash.set(message='Problem name can not be empty.')
        elif problem_form.vars.number_of_attempts == "":
            flash.set(message='Number of attempts can not be empty.')
        elif problem_form.vars.maximum_score == "":
            flash.set(message='Maximum score can not be empty.')
        else:
            if problem_form.vars.answer.strip() != "":
                exact_answer = 1
            else:
                exact_answer = 0
            teacher_id = auth.get_user()['id']
            deadline=datetime.datetime.strptime(problem_form.vars['deadline'].strip(), "%Y-%m-%dT%H:%M")
            pid = db.problem.insert(teacher_id=teacher_id, problem_description=problem_form.vars.problem_description, code=problem_form.vars.content,\
                answer=problem_form.vars.answer.strip(), problem_name=problem_form.vars.problem_name.strip(), max_points=problem_form.vars.maximum_score,\
                attempts=problem_form.vars.number_of_attempts, language=problem_form.vars.language,problem_uploaded_at=datetime.datetime.now(),\
                     exact_answer=exact_answer, deadline=deadline)
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
            users = [row['id'] for row in db(db.auth_user).select('id') if row['id']!=teacher_id]
            create_notification('Problem '+problem_form.vars.problem_name+' has been added.', users, deadline)
            redirect(URL('new_problem'))

    return dict(form=problem_form)