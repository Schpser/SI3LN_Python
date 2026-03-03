"""
Authentication decorator for Django Ninja endpoints
Requires valid JWT token for protected endpoints
"""

from functools import wraps
from ninja.security import HttpBearer
from .jwt_auth import JWTAuth


class JWTBearer(HttpBearer):
    """JWT Bearer authentication for Django Ninja"""
    
    def authenticate(self, request, token):
        """Authenticate request using JWT token"""
        if JWTAuth.is_blacklisted(token):
            return None
        user = JWTAuth.get_user_from_token(token)
        if user:
            request.user = user
            return user
        return None


# Create instance for use in routers
jwt_auth = JWTBearer()


def require_auth(func):
    """Decorator to require JWT authentication"""
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return {"error": "Authentication required"}, 401
        
        token = auth_header[7:]
        user = JWTAuth.get_user_from_token(token)
        
        if not user:
            return {"error": "Invalid or expired token. Please login again."}, 401
        
        request.user = user
        return func(request, *args, **kwargs)
    
    return wrapper
