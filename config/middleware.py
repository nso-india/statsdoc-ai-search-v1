"""
Custom middleware for handling various request processing issues.
"""

class FixDuplicateHostMiddleware:
    """
    Middleware to fix duplicate Host headers that can occur with certain proxy/load balancer configurations.
    
    Some proxy configurations can send duplicate host headers like:
    'mospiapi.edubildai.com,mospiapi.edubildai.com'
    
    This middleware cleans that up by taking only the first value.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Fix duplicate host header
        if 'HTTP_HOST' in request.META:
            host = request.META['HTTP_HOST']
            if ',' in host:
                # Take the first host value and strip whitespace
                first_host = host.split(',')[0].strip()
                request.META['HTTP_HOST'] = first_host
        
        response = self.get_response(request)
        return response


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to all HTTP responses.
    
    Implements the following security headers:
    - X-Content-Type-Options: Prevents MIME-sniffing
    - X-Frame-Options: Prevents clickjacking (already in Django but reinforced)
    - Content-Security-Policy: Restricts resource loading
    - Referrer-Policy: Controls referrer information
    - Permissions-Policy: Controls browser features
    - X-XSS-Protection: Legacy XSS protection (for older browsers)
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # X-Content-Type-Options: Prevent MIME-sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # X-Frame-Options: Prevent clickjacking
        if 'X-Frame-Options' not in response:
            response['X-Frame-Options'] = 'DENY'
        
        # Content-Security-Policy: Restrict resource loading
        # Adjust this policy based on your application needs
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' data: https://fonts.gstatic.com; "
            "connect-src 'self' https://api.openai.com https://mospi.edubildai.com https://mospiapi.edubildai.com https://statsdoc.ai.mospi.gov.in http://103.48.43.155 https://103.48.43.155; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        response['Content-Security-Policy'] = csp_policy
        
        # Referrer-Policy: Control referrer information
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions-Policy: Control browser features
        response['Permissions-Policy'] = (
            'geolocation=(), '
            'microphone=(self), '
            'camera=(), '
            'payment=(), '
            'usb=(), '
            'magnetometer=(), '
            'gyroscope=(), '
            'accelerometer=()'
        )
        
        # X-XSS-Protection: Legacy XSS protection for older browsers
        response['X-XSS-Protection'] = '1; mode=block'
        return response


class RestrictHTTPMethodsMiddleware:
    """
    Middleware to restrict HTTP methods and disable unnecessary ones.
    Only allows: GET, POST, PUT, PATCH, DELETE, OPTIONS
    Blocks: TRACE, TRACK, CONNECT, etc.
    """
    
    ALLOWED_METHODS = {'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS', 'HEAD'}
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the HTTP method is allowed
        if request.method not in self.ALLOWED_METHODS:
            from django.http import HttpResponseNotAllowed
            return HttpResponseNotAllowed(list(self.ALLOWED_METHODS))
        
        response = self.get_response(request)
        
        # Remove server version information
        if 'Server' in response:
            del response['Server']
        
        return response


class InputSanitizationMiddleware:
    """
    Middleware to sanitize and validate input parameters.
    Helps prevent parameter pollution and unexpected inputs.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Validate query parameters don't contain null bytes
        if request.GET:
            for key, value in request.GET.items():
                if '\x00' in key or (isinstance(value, str) and '\x00' in value):
                    from django.http import HttpResponseBadRequest
                    return HttpResponseBadRequest("Invalid characters in request parameters")
        
        # Sanitize POST data
        if request.POST:
            for key, value in request.POST.items():
                if '\x00' in key or (isinstance(value, str) and '\x00' in value):
                    from django.http import HttpResponseBadRequest
                    return HttpResponseBadRequest("Invalid characters in request data")
        
        response = self.get_response(request)
        return response
