from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrReadOnly(BasePermission):
    """
    Custom permission to only allow admin users to edit an object.
    Read-only access is allowed for any authenticated user.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

class IsOwnerOrAdmin(BasePermission):
    """
    Custom permission to only allow owners of an object or admin users to edit it.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.user == request.user

class IsTeacherOrAdminOrReadOnly(BasePermission):
    """
    Custom permission to only allow teachers or admin users to edit an object.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if request.user.is_staff:
            return True
        return hasattr(request.user, 'teacher') and obj.teacher == request.user.teacher
