from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwner(BasePermission):
    """Object-level permission that only allows owners of an object to access it."""

    def has_object_permission(self, request, view, obj):
        user_field = getattr(view, 'owner_field', 'user')
        owner = getattr(obj, user_field, None)
        if owner is None:
            return False
        return owner == request.user


class IsOwnerOrReadOnly(BasePermission):
    """Allow read-only for authenticated users, write only for owners."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        user_field = getattr(view, 'owner_field', 'user')
        owner = getattr(obj, user_field, None)
        if owner is None:
            return False
        return owner == request.user
