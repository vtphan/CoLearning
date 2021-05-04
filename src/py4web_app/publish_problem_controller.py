from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
from . import settings
from py4web.utils.form import Form, FormStyleBulma
import datetime
from pydal.validators import IS_IN_SET


from .utils import create_notification

@action('publish_problem/<problem_id>', method=['GET', 'POST'])
@action.uses(auth.user, 'publish_problem.html')
def publish_problem(problem_id):
    if 'teacher' not in groups.get(auth.get_user()['id']):
        redirect(URL('not_authorized'))
    problem = db.problem[problem_id]
    inclass_options = [
        5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60,
    ]
    inclass_labels = ['{} minutes'.format(m) for m in inclass_options ]
    homework_options = [
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14
    ]
    homework_labels = ['{} days'.format(d) for d in homework_options]
    homework_labels[0] = '1 day'

    if problem.type=='in-class':
        options, labels = inclass_options, inclass_labels
    else:
        options, labels = homework_options, homework_labels

    current_time = datetime.datetime.utcnow()
    if problem.deadline is None:
        publish_form = Form([
            Field('due_in', requires=IS_IN_SET(options, labels)),
        ])
        publish_form.param.submit_value = "Publish"
        if publish_form.accepted:
            due_in = int(publish_form.vars.due_in)
            if problem.type == 'in-class':
                deadline = current_time + datetime.timedelta(minutes=due_in)
            else:
                d = current_time + datetime.timedelta(days=due_in)
                deadline = datetime.datetime(d.year,d.month,d.day,hour=23,minute=59)
            db(db.problem.id==problem_id).update(deadline=deadline, published_at=current_time)
            flash.set('Problem has been published')
            redirect(URL('view_problem/'+str(problem_id)))
    else:
        publish_form = Form([
            Field('additional_time', requires=IS_IN_SET(options, labels)),
        ])
        publish_form.param.submit_value = "Republish"
        if publish_form.accepted:
            additional_time = int(publish_form.vars.additional_time)
            if problem.type == 'in-class':
                deadline = problem.deadline + datetime.timedelta(minutes=additional_time)
            else:
                d = problem.deadline + datetime.timedelta(days=additional_time)
                deadline = datetime.datetime(d.year,d.month,d.day,hour=23,minute=59)
            db(db.problem.id==problem_id).update(deadline=deadline)
            flash.set('Problem has been republished')
            redirect(URL('view_problem/'+str(problem_id)))
    return dict(form=publish_form, user_role='teacher', problem_id=problem_id)



# @action('publish_problem_inclass/<problem_id>', method=['GET', 'POST'])
# @action.uses(auth.user, 'publish_problem.html')
# def publish_problem_inclass(problem_id):
#     if 'teacher' not in groups.get(auth.get_user()['id']):
#         redirect(URL('not_authorized'))
#     problem = db.problem[problem_id]
#     if problem.deadline is None:
#         publish_form = Form([Field('alloted_time', requires=IS_IN_SET(['15 minutes', '30 minutes', '45 minutes', '60 minutes']),\
#              default='30 minutes', label='Due in')])
#         publish_form.param.submit_value = "Publish"
#     else:
#         publish_form = Form([Field('alloted_time', requires=IS_IN_SET(['5 minutes', '10 minutes', '15 minutes', '20 minutes', '25 minutes', '30 minutes']),\
#              default='5 minutes', label='Extend deadline by')])
#         publish_form.param.submit_value = "Republish"
#     if publish_form.accepted:
#         alloted_time = int(publish_form.vars.alloted_time[:-8])
#         if problem.deadline is None:
#             current_time = datetime.datetime.utcnow()
#             deadline = current_time + datetime.timedelta(minutes=alloted_time)
#             db(db.problem.id==problem_id).update(deadline=deadline, published_at=current_time)
#             flash.set('Problem has been published')
#         else:
#             deadline = problem.deadline + datetime.timedelta(minutes=alloted_time)
#             db(db.problem.id==problem_id).update(deadline=deadline)
#             flash.set('Problem has been republished')
#         redirect(URL('view_problem/'+str(problem_id)))
#     return dict(form=publish_form, user_role='instructor', problem_id=problem_id)

# @action('publish_problem_homework/<problem_id>', method=['GET', 'POST'])
# @action.uses(auth.user, 'publish_problem.html')
# def publish_problem_homework(problem_id):
#     if 'teacher' not in groups.get(auth.get_user()['id']):
#         redirect(URL('not_authorized'))
#     problem = db.problem[problem_id]
#     if problem.deadline is None:
#         publish_form = Form([Field('alloted_time', requires=IS_IN_SET(['1 day', '2 days', '3 days', '4 days', '5 days', '6 days', '7 days']),\
#              default='3 days', label='Due in')])
#         publish_form.param.submit_value = "Publish"
#     else:
#         publish_form = Form([Field('alloted_time', requires=IS_IN_SET(['1 hour', '6 hours', '12 hours', '1 day']),\
#              default='1 hour', label='Extend deadline by')])
#         publish_form.param.submit_value = "Republish"
#     if publish_form.accepted:
#         alloted_time = publish_form.vars.alloted_time
#         if alloted_time == "1 hour":
#             at = datetime.timedelta(hours=1)
#         elif alloted_time == "1 day":
#             at = datetime.timedelta(days=1)
#         elif alloted_time.endswith('hours'):
#             at = datetime.timedelta(hours=int(alloted_time[:-6]))
#         elif alloted_time.endswith('days'):
#             at = datetime.timedelta(days=int(alloted_time[:-5]))

#         if problem.deadline is None:
#             current_time = datetime.datetime.utcnow()
#             deadline = current_time + at
#             db(db.problem.id==problem_id).update(deadline=deadline, published_at=current_time)
#             flash.set('Problem has been published')
#         else:
#             deadline = problem.deadline + at
#             db(db.problem.id==problem_id).update(deadline=deadline)
#             flash.set('Problem has been republished')
#         redirect(URL('view_problem/'+str(problem_id)))
#     return dict(form=publish_form, user_role='instructor', problem_id=problem_id)

