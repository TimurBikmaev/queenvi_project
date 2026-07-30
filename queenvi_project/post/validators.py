from post.errors import UserCanReportError
from post.models import Report


class ReportValidator:
    def check_report(user, obj):
        """Оркестрация валидатораю"""
        ReportValidator.author_cannot_report(user, obj)
        ReportValidator.staff_cannot_report(user)
        ReportValidator.report_banned(obj)
        ReportValidator.report_already_exists(user, obj)

    @staticmethod
    def author_cannot_report(user, obj):
        """Юзер не может зарепортить свой же созданный объект."""
        if obj.user == user:
            raise UserCanReportError()

    @staticmethod
    def staff_cannot_report(user):
        """Модер и стример не могут репортить, ведь они могут сразу банить."""
        if not user.is_user:
            raise UserCanReportError(staff=True)

    @staticmethod
    def report_banned(obj):
        """Юзер не может зарепортить забаненный объект."""
        if obj.is_banned:
            raise UserCanReportError(banned=True)

    @staticmethod
    def report_already_exists(user, obj):
        """Юзер не может дважды зарепортить один и тот же объект."""
        if Report.objects.filter(user=user, post=obj).exists():
            raise UserCanReportError(the_same_obj=True)
