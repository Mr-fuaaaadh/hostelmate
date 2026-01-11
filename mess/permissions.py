from rest_framework import permissions

class IsMessOwner(permissions.BasePermission):
    """
    Allow access only to users with role 'MESS_OWNER'.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, "is_mess_owner", False)

class IsOwnerOfHome(permissions.BasePermission):
    """
    Object-level permission to only allow mess owners to access their own homes.
    """
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user
