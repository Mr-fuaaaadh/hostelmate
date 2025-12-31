from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """Allow only owners of the hostel to edit the room."""
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.hostel.owner == request.user

class IsAdminOrReadOnly(permissions.BasePermission):
    """Allow admin users to edit, others read-only."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff
