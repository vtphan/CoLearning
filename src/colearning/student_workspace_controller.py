from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
from . import settings
from py4web.utils.form import Form, FormStyleBulma
import datetime

from .utils import create_notification

@action('student_workspace/<student_id>/<problem_id>', method=['GET', 'POST'])
@action.uses(auth.user, 'student_workspace.html')
def workspace(student_id, problem_id):
        user_id = auth.get_user()['id']
        if 'student' not in groups.get(user_id):
                redirect(URL('not_authorized'))

        problem, workspace, submissions, messages = get_workspace_info(student_id, problem_id)

        student_name = auth.get_user()['first_name']
        help_form = Form([Field('question', type='text')])
        if help_form.accepted:
                message_id = db.help_seeking_message.insert(student_id=user_id, problem_id=problem.id, message=help_form.vars.question,\
                        submitted_at=datetime.datetime.now())
                db.help_seeking_message_queue.insert(message_id=message_id)
                db.commit()
                create_notification("New help seeking message recieved.", recipients=[ user['id'] for user in db(db.auth_user).select('id') if 'teacher' in groups.get(user['id'])],\
                        expire_at=problem.deadline)
        return dict(problem=problem, workspace=workspace, time_interval=30000, submissions=submissions, student_name=student_name, student_id=student_id, help_form=help_form, messages=messages)

@action('student_workspace_view/<student_id>/<problem_id>', method='GET')
@action.uses(auth.user, 'student_workspace_view.html')
def workspace_view(student_id, problem_id):
        user_id = auth.get_user()['id']
        if 'teacher' not in groups.get(user_id):
                redirect(URL('not_authorized'))
        problem, workspace, submissions, messages = get_workspace_info(student_id, problem_id)
        student_name = db.auth_user[student_id].first_name
        return dict(problem=problem, workspace=workspace, time_interval=1000, submissions=submissions, student_name=student_name, student_id=student_id, messages=messages)

def get_workspace_info(student_id, problem_id):
        problem = db.problem[problem_id]
        workspace = db((db.student_workspace.problem_id==problem_id) & (db.student_workspace.student_id==student_id)).select()
        if workspace is None or len(workspace)==0:
                db.student_workspace.insert(problem_id=problem_id, student_id=student_id, content=problem.code, attempt_left=problem.attempts)
                db.commit()
                workspace = db((db.student_workspace.problem_id==problem_id) & (db.student_workspace.student_id==student_id)).select().first()
        else:
                workspace = workspace.first()

        submissions = db.executesql("select s.id as id, s.content as submission, s.submitted_at, s.submission_category, v.verdict, v.score, f.content as feedback\
                from submission s left join submission_verdict v on s.id=v.submission_id left join feedback f on s.id=f.submission_id where \
                        s.problem_id="+str(problem_id)+" and s.student_id="+str(student_id), as_dict=True)
        messages = db((db.help_seeking_message.student_id==student_id)&(db.help_seeking_message.problem_id==problem_id)&(db.help_seeking_message.submission_id==None)).select()
        # feedbacks = db.executesql("select s.id, s.content, f.content as feedback from feedback f, submission s where f.submission_id==s.id and s.student_id=%d and s.problem_id=%d" % (student_id, problem_id))
        # feedbacks = db((db.feedback.submission_id==db.submission.id)&(db.submission.student_id==student_id)&(db.submission.problem_id==problem_id)).select(db.submission.id, db.submission.content, db.feedback.content)
        # print(datetime.datetime.now(), feedbacks)
        return problem, workspace, submissions, messages