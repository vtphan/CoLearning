"""
This file defines actions, i.e. functions the URLs are mapped into
The @action(path) decorator exposed the function at URL:

    http://127.0.0.1:8000/{app_name}/{path}

If app_name == '_default' then simply

    http://127.0.0.1:8000/{path}

If path == 'index' it can be omitted:

    http://127.0.0.1:8000/

The path follows the bottlepy syntax.

@action.uses('generic.html')  indicates that the action uses the generic.html template
@action.uses(session)         indicates that the action uses the session
@action.uses(db)              indicates that the action uses the db
@action.uses(T)               indicates that the action uses the i18n & pluralization
@action.uses(auth.user)       indicates that the action requires a logged in user
@action.uses(auth)            indicates that the action requires the auth object

session, db, T, auth, and tempates are examples of Fixtures.
Warning: Fixtures MUST be declared with @action.uses({fixtures}) else your app will result in undefined behavior
"""

from pydal.validators import IS_NOT_EMPTY, IS_INT_IN_RANGE, IS_IN_SET, IS_IN_DB
from py4web.utils.form import Form, FormStyleBulma
from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from .common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash

from .activation_controller import *
from .new_problem_controller import *
from .workspace_controller import *
from .active_problems_controller import *
from .submissions_controller import *
from .workspace_viewer_controller import *
from .problem_list_controller import *
from .edit_problem_controller import *
from .student_workspace_list_controller import *
from .notification_controller import *
from .global_value_controller import *
from .student_workspace_controller import *
from .help_message_view_controller import *

from .problem_loader_controller import *
from .feedback_controller import *
from .view_problem_controller import *
from .publish_problem_controller import *
# from .test_controller import *
from .run_query_controller import *
from .statistics_controller import *
from .first_user_controller import *


@action("index", method='GET')
@action.uses(auth, "index.html")
def index():
    if db(db.auth_user).select().first() is None:
        redirect(URL('create_first_user'))
    user = auth.get_user()
    if user:
        user_groups = groups.get(auth.get_user()['id'])
        if 'teacher' in user_groups or 'ta' in user_groups:
            redirect(URL('problem_list', vars=dict(type='published')))
        else:
            redirect(URL('active_problems'))
    else:
        redirect(URL('auth/login'))


@unauthenticated("not_authorized", "not_authorized.html")
def not_authorized():
    return dict()

@unauthenticated("check_address")
def check_address():
    return "correct"

@unauthenticated("get_app_id")
def get_app_id():
    return settings.APP_NAME