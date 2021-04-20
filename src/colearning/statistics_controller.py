from py4web import action, request, Field,redirect, URL
from .common import db, groups, auth
from py4web.utils.form import Form, FormStyleBulma
import datetime
import json
from .utils import create_notification, is_eligible_for_help

@action('statistics', method='GET')
@action.uses(auth.user, 'statistics.html')
def statistics():
    user_id = auth.get_user()['id']
    grp = groups.get(user_id)
    if 'teacher' in grp:
        user_role = 'instructor'
    elif 'ta' in grp:
        user_role = 'ta'
    elif 'student' in grp:
        user_role = 'student'
    else:
        redirect(URL('not_authorized'))
    total_likes = db((db.comment_like.comment_id==db.comment.id)&(db.comment.author_id==user_id)).count()
    total_likes += db((db.comment_like.comment_id==None)&(db.comment_like.discussion_id==db.discussion.id)& (db.discussion.author_id==user_id)).count()
    if user_role == 'student':
        problems = db(db.problem).select()
        p = []
        for problem in problems:
            d = [problem.problem_name]
            verdicts = db((db.submission.problem_id==problem.id)&(db.submission_verdict.submission_id==db.submission.id)&(db.submission.student_id==user_id)).select()
            max_score = 0
            correct = False
            for v in verdicts:
                if v.submission_verdict.verdict == "correct":
                    d.append("Graded correct")
                    d.append(v.submission.submitted_at.date())
                    d.append(v.submission_verdict.score)
                    correct = True
                    break
                max_score = max(max_score, v.submission_verdict.score)
                dt = v.submission.submitted_at.date()

            if len(verdicts) == 0:
                d.append("Not submitted")
                d.append("-")
                d.append("-")
            elif correct == False:
                d.append("Graded incorrect")
                d.append(dt)
                d.append(max_score)
            p.append(d)

    else:
        p = db(db.problem.teacher_id==user_id).select()
    return dict(user_role=user_role, total_likes=total_likes, problems = p)