"""
Middleware for extracting client fingerprint from request headers.
"""


class ClientFingerprintMiddleware:
    """
    Middleware to extract X-Client-Fingerprint header and attach it to the request object.
    
    This middleware adds a `client_fingerprint` attribute to the request object,
    making it easily accessible in all views.
    
    The X-Client-Fingerprint header is optional and will be None if not provided.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        client_fingerprint = request.META.get('HTTP_X_CLIENT_FINGERPRINT')
        request.client_fingerprint = client_fingerprint
        
        response = self.get_response(request)
        return response
