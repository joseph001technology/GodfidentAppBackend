from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """Object-level permission that only allows the owner of a record to access it.

    Works for any model in this app that has a `user` FK: Note, Folder,
    Topic, Rule, RuleCategory.
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


# Kept as aliases so existing imports elsewhere in the codebase don't break.
IsNoteOwner = IsOwner
IsFolderOwner = IsOwner
IsTopicOwner = IsOwner
IsRuleOwner = IsOwner
IsRuleCategoryOwner = IsOwner