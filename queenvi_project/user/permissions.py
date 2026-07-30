from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwner(BasePermission):
    """Изменение доступно только владельцу."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.user == request.user


class IsModerOrStreamer(BasePermission):
    """Доступ разрешен только модератору или стримеру."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and (request.user.is_moderator or request.user.is_streamer)
        )
