from rest_framework import permissions

class IsRegionalManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'regional_manager'

    def has_object_permission(self, request, view, obj):
        return request.user.region == getattr(obj, 'region', None) or \
               request.user.region == getattr(obj.creator, 'region', None)

class IsGlobalManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'global_manager'

class IsEmployee(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'employee'

class IsIdeaCreator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.creator == request.user

class CanManageIdea(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'global_manager':
            return True
        if request.user.role == 'regional_manager':
            return obj.creator.region == request.user.region
        return obj.creator == request.user
