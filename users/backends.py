from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

UserModel = get_user_model()

class EmailBackend(ModelBackend):
    """
    Custom authentication backend to allow login with email
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        import logging
        logger = logging.getLogger('users')
        
        logger.debug(f"EmailBackend.authenticate called with username: {username}")
        
        if username is None or password is None:
            logger.debug("Username or password is None, authentication failed")
            return None
            
        try:
            # First try exact email match
            logger.debug(f"Trying exact email match for: {username}")
            user = UserModel.objects.get(email=username)
            logger.debug(f"Found user with exact email match: {user.email}")
            
            if user.check_password(password):
                logger.debug(f"Password check successful for user: {user.email}")
                return user
            else:
                # Password doesn't match
                logger.debug(f"Password check failed for user: {user.email}")
                return None
        except UserModel.DoesNotExist:
            # Try case-insensitive email match
            logger.debug(f"No exact email match, trying case-insensitive match for: {username}")
            try:
                user = UserModel.objects.get(email__iexact=username)
                logger.debug(f"Found user with case-insensitive email match: {user.email}")
                
                if user.check_password(password):
                    logger.debug(f"Password check successful for user: {user.email}")
                    return user
                else:
                    logger.debug(f"Password check failed for user: {user.email}")
                    return None
            except UserModel.DoesNotExist:
                # No user was found with this email
                logger.debug(f"No user found with email (case-insensitive): {username}")
                return None
        
    def get_user(self, user_id):
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None