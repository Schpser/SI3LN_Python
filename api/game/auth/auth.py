from ninja.security import HttpBearer
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
import secrets


class TokenManager:
    """Simple token manager for development"""
    _tokens = {}  # In production, use Redis or database
    
    @classmethod
    def create_token(cls, user: User) -> str:
        token = secrets.token_urlsafe(32)
        cls._tokens[token] = user.id
        return token
    
    @classmethod
    def get_user_id(cls, token: str) -> int:
        return cls._tokens.get(token)
    
    @classmethod
    def delete_token(cls, token: str):
        if token in cls._tokens:
            del cls._tokens[token]


class AuthBearer(HttpBearer):
    """Bearer token authentication"""
    
    def authenticate(self, request, token):
        user_id = TokenManager.get_user_id(token)
        if user_id:
            try:
                return User.objects.get(id=user_id)
            except User.DoesNotExist:
                return None
        return None
