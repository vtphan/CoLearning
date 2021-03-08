from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
from . import settings

import datetime
import json

@action('get_problem_info', method='GET')
@action.uses(auth.user)
def get_problem_info():
    problem_info = db(db.problem.deadline>datetime.datetime.utcnow()).select(db.problem.id, db.problem.problem_name).as_list()
    return json.dumps(problem_info)

@action('load_problem/<problem_id>', method='GET')
@action.uses(auth.user)
def load_problem(problem_id):
    if 'student' not in groups.get(auth.get_user()['id']):
        return None
    student_id = auth.get_user()['id']
    problem = db(db.problem.id==problem_id).select(db.problem.problem_name, db.problem.code, db.problem.language, db.problem.attempts).as_list()[0]

    workspace = db((db.student_workspace.problem_id==problem_id) & (db.student_workspace.student_id==student_id)).select(db.student_workspace.content, db.student_workspace.comment)
    if workspace is None or len(workspace)==0:
            db.student_workspace.insert(problem_id=problem_id, student_id=student_id, content=problem['code'], comment="", attempt_left=problem['attempts'])
            db.commit()
            workspace = db((db.student_workspace.problem_id==problem_id) & (db.student_workspace.student_id==student_id)).select(db.student_workspace.content, db.student_workspace.comment).first()
    else:
            workspace = workspace.first()
    problem['code'] = workspace['content']
    problem['comment'] = workspace['comment']
    return json.dumps(problem)