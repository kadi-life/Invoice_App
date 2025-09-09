from django.utils.deprecation import MiddlewareMixin

class CacheControlMiddleware(MiddlewareMixin):
    """
    Middleware to add cache control headers to all authenticated responses
    to prevent browser back button issues after logout.
    """
    
    def process_response(self, request, response):
        # Skip static and media files
        path = request.path_info.lstrip('/')
        if path.startswith('static/') or path.startswith('media/'):
            return response
            
        # Add cache control headers to all authenticated requests
        if request.user.is_authenticated:
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        return response