from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Only the owner can edit/delete an object.
    Read-only for others.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Admins can edit/delete. Others read-only.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff
