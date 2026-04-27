from rest_framework.permissions import BasePermission


class IsStaffUser(BasePermission):
    """
    Custom permission to only allow staff users to access the view.
    """
    
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.is_staff
        )


class CanManageUsers(BasePermission):
    """
    Custom permission for user management operations.
    Only staff users can manage other users, with restrictions:
    - Staff cannot delete/deactivate themselves
    - Only superusers can manage other superusers
    """
    
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.is_staff
        )
    
    def has_object_permission(self, request, view, obj):
        # Staff users can view any user
        if request.method == 'GET':
            return True
            
        # Prevent staff from deleting/deactivating themselves
        if obj == request.user and request.method in ['DELETE', 'POST']:
            # Check if it's a deactivation endpoint
            if 'deactivate' in request.path:
                return False
            # Check if it's a deletion
            if request.method == 'DELETE':
                return False
                
        # Only superusers can manage other superusers
        if obj.is_superuser and not request.user.is_superuser:
            return False
            
        return True
