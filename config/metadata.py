"""
Custom metadata class to limit information exposure in OPTIONS responses.
Security fix for CWE-74: Insecure HTTP Method Allowed
"""
from rest_framework.metadata import SimpleMetadata


class MinimalMetadata(SimpleMetadata):
    """
    Custom metadata class that returns minimal information in OPTIONS responses.
    This prevents detailed API schema exposure for security.
    """
    
    def determine_metadata(self, request, view):
        """
        Return minimal metadata that doesn't expose detailed schema information.
        Only returns allowed HTTP methods.
        """
        metadata = {
            'name': view.get_view_name(),
            'description': view.get_view_description(),
        }
        
        # Only include allowed methods, no field schema
        if hasattr(view, 'allowed_methods'):
            metadata['allowed_methods'] = view.allowed_methods
        
        return metadata
