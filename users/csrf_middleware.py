from django.middleware.csrf import CsrfViewMiddleware
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class EnhancedCsrfMiddleware(CsrfViewMiddleware):
    """
    Enhanced CSRF middleware that provides better error logging for production environments
    to help diagnose CSRF token issues.
    """
    
    def process_view(self, request, callback, callback_args, callback_kwargs):
        # Call the parent method to perform the actual CSRF check
        result = super().process_view(request, callback, callback_args, callback_kwargs)
        
        # If there was a CSRF error, log additional information
        if result is not None and result.status_code == 403:
            # Log detailed information about the request
            logger.warning(
                "CSRF verification failed. Request path: %s, Method: %s, Referrer: %s",
                request.path,
                request.method,
                request.META.get('HTTP_REFERER', 'No referrer')
            )
            
            # Check if the CSRF token is in the request
            csrf_token = request.META.get('CSRF_COOKIE', None)
            if csrf_token is None:
                logger.warning("CSRF cookie not present in the request")
            
            # Check if the CSRF token is in the POST data
            post_token = request.POST.get('csrfmiddlewaretoken', None)
            if post_token is None:
                logger.warning("CSRF token not present in POST data")
            elif csrf_token != post_token:
                logger.warning("CSRF token mismatch between cookie and POST data")
        
        return result