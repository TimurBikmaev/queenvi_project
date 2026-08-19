from uuid import uuid4

from core.constants import PublicIdConstants


def generate_public_id():
    return uuid4().hex[:PublicIdConstants.MAX_LENGTH]


def get_queryset_by_filter_is_banned(user, request, model, action=None):
    """Возвращает кверисет в зависимости от выбранного параметра is_banned."""
    is_banned = False

    if user.is_authenticated and not user.is_user:
        param_is_banned = request.query_params.get('is_banned', '').lower()

        if param_is_banned == 'true':
            is_banned = True

        elif (
            param_is_banned == 'all'
            or action in ('retrieve', 'partial_update')
        ):
            return model.objects.all()

    return model.objects.filter(is_banned=is_banned)
