from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

UserModel = get_user_model()

class EmailBackend(ModelBackend):
    """
    Custom authentication backend to allow login with email
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
            
        try:
            # First try exact email match
            user = UserModel.objects.get(email=username)
            if user.check_password(password):
                return user
            else:
                # Password doesn't match
                return None
        except UserModel.DoesNotExist:
            # Try case-insensitive email match
            try:
                user = UserModel.objects.get(email__iexact=username)
                if user.check_password(password):
                    return user
                else:
                    return None
            except UserModel.DoesNotExist:
                # No user was found with this email
                return None
        
    def get_user(self, user_id):
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None