from rest_framework import permissions


class IsNoteOwner(permissions.BasePermission):
    """Object-level permission that only allows owners of a note to access it."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsFolderOwner(permissions.BasePermission):
    """Object-level permission for folders."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsTopicOwner(permissions.BasePermission):
    """Object-level permission for topics."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
