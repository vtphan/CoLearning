
from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
from . import settings
from py4web.utils.form import Form, FormStyleBulma
import datetime
import json
from .utils import create_notification

@action('student_workspace/<student_id>/<problem_id>', method=['GET', 'POST'])
@action.uses(auth.user, 'student_workspace.html')
def workspace(student_id, problem_id):
        user_id = auth.get_user()['id']
        if 'student' not in groups.get(user_id):
                redirect(URL('not_authorized'))

        problem, workspace, submissions, messages, feedbacks = get_workspace_info(student_id, problem_id)

        student_name = auth.get_user()['first_name']
        help_form = Form([Field('question', type='text')])
        if help_form.accepted:
                db.help_queue.insert(student_id=user_id, problem_id=problem.id, message=help_form.vars.question, asked_at=datetime.datetime.now())
                db.commit()
                create_notification("New help seeking message recieved.", recipients=[ user['id'] for user in db(db.auth_user).select('id') if 'teacher' in groups.get(user['id'])],\
                        expire_at=problem.deadline)
        return dict(problem=problem, workspace=workspace, time_interval=30000, submissions=submissions, student_name=student_name, student_id=student_id, help_form=help_form, messages=messages, feedbacks=feedbacks)

@action('student_workspace_view/<student_id>/<problem_id>', method='GET')
@action.uses(auth.user, 'student_workspace_view.html')
def workspace_view(student_id, problem_id):
        user_id = auth.get_user()['id']
        if 'teacher' not in groups.get(user_id):
                redirect(URL('not_authorized'))
        ref = request.get_header('Referer')
        if ref is not None:
                ref = ref.split('/')
        help_message_id = 0
        if ref is not None and len(ref)>2 and ref[-2]=='view_help_message':
                help_message_id = int(ref[-1])
                if db.help_queue[help_message_id].status == "opened":
                        db(db.help_queue.id==help_message_id).update(status='viewed')
                        db.commit()
        problem, workspace, submissions, messages, feedbacks = get_workspace_info(student_id, problem_id)
        student_name = db.auth_user[student_id].first_name
        return dict(problem=problem, workspace=workspace, time_interval=1000, submissions=submissions,\
                 student_name=student_name, student_id=student_id, messages=messages, feedbacks=feedbacks,\
                          help_message_id=help_message_id)

def get_workspace_info(student_id, problem_id):
        problem = db.problem[problem_id]
        workspace = db((db.student_workspace.problem_id==problem_id) & (db.student_workspace.student_id==student_id)).select()
        if workspace is None or len(workspace)==0:
                db.student_workspace.insert(problem_id=problem_id, student_id=student_id, content=problem.code, attempt_left=problem.attempts)
                db.commit()
                workspace = db((db.student_workspace.problem_id==problem_id) & (db.student_workspace.student_id==student_id)).select().first()
        else:
                workspace = workspace.first()

        # submissions = db.executesql("select s.id as id, s.content as submission, s.submitted_at, s.submission_category, v.verdict, v.score, f.content as feedback\
        #         from submission s left join submission_verdict v on s.id=v.submission_id left join feedback f on s.id=f.submission_id where \
        #                 s.problem_id="+str(problem_id)+" and s.student_id="+str(student_id)+" order by s.submitted_at desc", as_dict=True)
        submissions = db((db.submission.student_id==student_id)&(db.submission.problem_id==problem_id)).select(db.submission.id, orderby=~db.submission.submitted_at)
        messages = db((db.help_seeking_message.student_id==student_id)&(db.help_seeking_message.problem_id==problem_id)&(db.help_seeking_message.submission_id==None)).select()
        feedbacks = db.executesql("select id, given_at from feedback where problem_id="+str(problem_id)+" and submission_id is NULL order by given_at desc", as_dict=True)
        return problem, workspace, submissions, messages, feedbacks


@action('get_student_code/<workspace_id>', method='GET')
@action.uses(auth.user)
def get_student_code(workspace_id):
        user_id = auth.get_user()['id']
        ws = db.student_workspace[workspace_id].as_dict()
        if 'teacher' in groups.get(user_id):
                return json.dumps(ws, default=str)
        if 'student' in groups.get(user_id) and user_id == ws['student_id']:
                return json.dumps(ws, default=str)
        redirect(URL('not_authorized'))