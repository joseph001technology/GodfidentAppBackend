from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """Object-level permission that only allows the owner of a record to access it."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


# Kept as aliases so existing imports elsewhere in the codebase don't break.
IsNoteOwner = IsOwner
IsFolderOwner = IsOwner
IsTopicOwner = IsOwner