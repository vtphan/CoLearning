from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
from . import settings
from py4web.utils.form import Form, FormStyleBulma
import datetime
from pydal.validators import IS_IN_SET

from .utils import create_notification, add_global_value

@action('new_inclass_problem', method=['GET', 'POST'])
@action.uses(auth.user, 'new_problem.html', flash)
def new_inclass_problem():
    if not 'teacher' in groups.get(auth.get_user()['id']):
        redirect(URL('not_authorized'))
    default_lang = db(db.global_value.variable=='language').select()
    if len(default_lang) == 0:
        default_lang = "Python"
    else:
        default_lang = default_lang.first()['value']
    problem_form = Form(
        [
            Field('problem_name', required=True, default='assignment_'+datetime.datetime.utcnow().strftime("%Y%m%d%M%S")),
            Field('alloted_time', requires=IS_IN_SET(["15 minutes", "30 minutes", "45 minutes", "60 minutes"]), default="30 minutes"),
            Field('number_of_attempts', type='integer', default=1),
            Field('maximum_score', type='integer', default=10),
            Field('problem_description', 'text'),
            Field('language', requires=IS_IN_SET(['Python', 'Java', 'C++']), default=default_lang),
            Field('content', 'text'),
            Field('answer'),
            Field('topics'),
            Field('publish', type='boolean')
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
            # deadline=datetime.datetime.strptime(problem_form.vars['deadline'].strip(), "%Y-%m-%dT%H:%M")
            dl = problem_form.vars['alloted_time']
            dl = int(dl[:2])
            
            pid = db.problem.insert(teacher_id=teacher_id, problem_description=problem_form.vars.problem_description, code=problem_form.vars.content,\
                answer=problem_form.vars.answer.strip(), problem_name=problem_form.vars.problem_name.strip(), max_points=problem_form.vars.maximum_score,\
                attempts=problem_form.vars.number_of_attempts, language=problem_form.vars.language,problem_uploaded_at=datetime.datetime.utcnow(),\
                     exact_answer=exact_answer, alloted_time=dl, type="in-class")
            deadline=None
            
            if problem_form.vars.publish == 'ON':
                deadline = datetime.datetime.utcnow() + datetime.timedelta(minutes=dl)
                db.problem[pid] = dict(deadline=deadline)

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

    return dict(form=problem_form)


@action('new_homework_problem', method=['GET', 'POST'])
@action.uses(auth.user, 'new_problem.html', flash)
def new_homework_problem():
    if not 'teacher' in groups.get(auth.get_user()['id']):
        redirect(URL('not_authorized'))
    default_lang = db(db.global_value.variable=='language').select()
    if len(default_lang) == 0:
        default_lang = "Python"
    else:
        default_lang = default_lang.first()['value']
    problem_form = Form(
        [
            Field('problem_name', required=True, default='assignment_'+datetime.datetime.utcnow().strftime("%Y%m%d%M%S")),
            Field('deadline', requires=IS_IN_SET(["1 day", "2 days", "3 days", "4 days", "5 days", "6 days", "7 days"]), default="3 days"),
            Field('number_of_attempts', type='integer', default=1),
            Field('maximum_score', type='integer', default=10),
            Field('problem_description', 'text'),
            Field('language', requires=IS_IN_SET(['Python', 'Java', 'C++']), default=default_lang),
            Field('content', 'text'),
            Field('answer'),
            Field('topics'),
            Field('publish', type='boolean')
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
            # deadline=datetime.datetime.strptime(problem_form.vars['deadline'].strip(), "%Y-%m-%dT%H:%M")
            dl = problem_form.vars['deadline']
            dl = int(dl[:1])
            
            pid = db.problem.insert(teacher_id=teacher_id, problem_description=problem_form.vars.problem_description, code=problem_form.vars.content,\
                answer=problem_form.vars.answer.strip(), problem_name=problem_form.vars.problem_name.strip(), max_points=problem_form.vars.maximum_score,\
                attempts=problem_form.vars.number_of_attempts, language=problem_form.vars.language,problem_uploaded_at=datetime.datetime.utcnow(),\
                     exact_answer=exact_answer, alloted_time=dl, type="homework")
            deadline = None
            if problem_form.vars.publish=='ON':
                deadline = datetime.datetime.utcnow() + datetime.timedelta(days=dl)
                db.problem[pid] = dict(deadline=deadline)

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
                create_notification('New homework assignment '+problem_form.vars.problem_name+' has been added.', users, deadline)
            redirect(URL('view_problem/'+str(pid)))

    return dict(form=problem_form)

@action('publish_problem/<problem_id>')
@action.uses(auth.user)
def publish_problem(problem_id):
    problem = db.problem[problem_id]
    if problem.type=='in-class':
        deadline = datetime.datetime.utcnow() + datetime.timedelta(minutes=problem.alloted_time)
    elif problem.type=='homework':
        deadline = datetime.datetime.utcnow() + datetime.timedelta(days=problem.alloted_time)
    db.problem[problem_id] = dict(deadline=deadline)
    db.commit()
    return "Problem has been published!"