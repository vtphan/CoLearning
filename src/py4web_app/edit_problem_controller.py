from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
from . import settings
from py4web.utils.form import Form, FormStyleBulma
import datetime
from pydal.validators import IS_IN_SET, IS_NOT_EMPTY, IS_INT_IN_RANGE

from .utils import create_notification

@action('edit_problem/<problem_id>', method=['GET', 'POST'])
@action.uses(auth.user, 'edit_problem.html', flash)
def edit_problem(problem_id):
    teacher_id = auth.get_user()['id']
    if 'teacher' in groups.get(teacher_id):
        user_role = 'teacher'
    elif 'ta' in groups.get(teacher_id):
        user_role = 'ta'
    else:
        redirect(URL('not_authorized'))
    problem = db.problem[problem_id]
    topics = db(db.problem_topic.problem_id==problem_id).select()
    topics = ",".join([db.topic[t.topic_id].topic_description for t in topics])
    
    problem_form = Form(
        [
            Field('problem_name', requires=IS_NOT_EMPTY(), default=problem.problem_name),
            Field('number_of_attempts', requires=IS_INT_IN_RANGE(1,11), default=problem.attempts),
            Field('maximum_score', requires=IS_INT_IN_RANGE(1,101), default=problem.max_points),
            Field('problem_description', 'text', requires=IS_NOT_EMPTY(), default=problem.problem_description),
            Field('helper_code', 'text', default=problem.code),
            Field('language', requires=IS_IN_SET(['Python', 'Java', 'C++']), default=problem.language),
            Field('problem_type', requires=IS_IN_SET(['in-class','homework']), default=problem.type),
            Field('answer', default=problem.answer),
            Field('topics', default=topics),
        ], 
        formstyle=FormStyleBulma,
    )
    problem_form.param.submit_value="Update"
    if problem_form.accepted:
        if problem_form.vars.answer.strip() != "":
            exact_answer = 1
        else:
            exact_answer = 0
        
        # deadline=datetime.datetime.strptime(problem_form.vars['deadline'].strip(), "%Y-%m-%dT%H:%M")
        db(db.problem.id==problem_id).update(
            code=problem_form.vars.helper_code, 
            problem_description=problem_form.vars.problem_description, 
            answer=problem_form.vars.answer.strip(),
            problem_name=problem_form.vars.problem_name.strip(), 
            max_points=problem_form.vars.maximum_score, 
            attempts=problem_form.vars.number_of_attempts,
            language=problem_form.vars.language,
            type=problem_form.vars.problem_type,
            last_updated_at=datetime.datetime.utcnow(), 
            exact_answer=exact_answer)
        new_topics = problem_form.vars.topics.strip()
        if new_topics != topics:
            db(db.problem_topic.problem_id==problem_id).delete()
            topics = new_topics
            if topics != "":
                for topic in topics.split(','):
                    tmp = db(db.topic.topic_description==topic).select()
                    if len(tmp)==0:
                        topic_id = db.topic.insert(topic_description=topic)
                    else:
                        topic_id = tmp.first()['id']
                    db.problem_topic.insert(problem_id=problem_id, topic_id=topic_id)
        db.commit()
        flash.set('Problem '+problem_form.vars.problem_name.strip()+' has been updated successfully.')
        users = [row['id'] for row in db(db.auth_user).select('id') if row['id']!=teacher_id]
        if problem.deadline is not None:
            create_notification('Problem '+problem_form.vars.problem_name+' has been updated. Please reload!', users, problem.deadline)
        redirect(URL('view_problem/'+problem_id))

    return dict(form=problem_form, user_role=user_role)

