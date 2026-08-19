import logging

from post.errors import UserCanReportError
from post.models import Report


logger = logging.getLogger(__name__)


class ReportValidator:
    def check_report(user, obj):
        """Оркестрация валидатораю"""
        ReportValidator.author_cannot_report(user, obj)
        ReportValidator.staff_cannot_report(user)
        ReportValidator.report_banned(user, obj)
        ReportValidator.report_already_exists(user, obj)

    @staticmethod
    def author_cannot_report(user, obj):
        """Юзер не может зарепортить свой же созданный объект."""
        if obj.user == user:
            logger.warning(
                'Юзер %s (%s) попытался зарепортить свой объект %s',
                user.username,
                user.role,
                obj.public_id
            )
            raise UserCanReportError()

    @staticmethod
    def staff_cannot_report(user):
        """Модер и стример не могут репортить, ведь они могут сразу банить."""
        if not user.is_user:
            logger.warning(
                'Модер или стример %s (%s) попытался кинуть репорт',
                user.username,
                user.role,
            )
            raise UserCanReportError(staff=True)

    @staticmethod
    def report_banned(user, obj):
        """Юзер не может зарепортить забаненный объект."""
        if obj.is_banned:
            logger.warning(
                'Юзер %s (%s) попытался зарепортить '
                'забаненный объект %s, is_banned = %s',
                user.username,
                user.role,
                obj.public_id,
                obj.is_banned
            )
            raise UserCanReportError(banned=True)

    @staticmethod
    def report_already_exists(user, obj):
        """Юзер не может дважды зарепортить один и тот же объект."""
        if Report.objects.filter(user=user, post=obj).exists():
            logger.warning(
                'Юзер %s (%s) попытался дважды зарепортить '
                'один и тот же объект %s',
                user.username,
                user.role,
                obj.public_id
            )
            raise UserCanReportError(the_same_obj=True)
