from post.errors import UserCanReportError
from post.models import Report


def can_user_report_post(user, post):
    if post.user == user:
        raise UserCanReportError(the_same_post=False)
    if Report.objects.filter(user=user, post=post).exists():
        raise UserCanReportError(the_same_post=True)
