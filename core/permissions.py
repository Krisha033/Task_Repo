from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allow full access for staff/admin, read-only for authenticated non-admin users.
    """

    def has_permission(self, request, view):
        # only allow read for non-admins, write for staff
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    For Task: allow owner or admin to modify; others read-only.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user and request.user.is_staff:
            return True
        return obj.assigned_user == request.user
