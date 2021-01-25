from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth, flash
from . import settings
from py4web.utils.form import Form, FormStyleBulma
import datetime
from pydal.validators import IS_IN_SET

from .utils import create_notification

@action('view_problem/<problem_id>', method='GET')
@action.uses(auth.user, 'view_problem.html')
def view_problem(problem_id):
    problem = db.problem[problem_id].as_dict()
    topics = db((db.problem_topic.problem_id==problem_id)&(db.topic.id==db.problem_topic.topic_id)).select(db.topic.topic_description)
    problem['topics'] = ", ".join([row['topic_description'] for row in topics])
    
    return problem