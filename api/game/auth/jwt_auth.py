"""
JWT Authentication with Pepper for SI3LN API
Tokens expire after 24 hours
"""

import jwt
import hashlib
import hmac
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.models import User
from typing import Optional, Dict, Any
import os
import uuid

# Redis-backed token blacklist (shared across all workers)
try:
    import redis as _redis_lib
    _redis_client = _redis_lib.from_url(
        os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )
    _redis_client.ping()  # verify connection at startup
    _USE_REDIS_BLACKLIST = True
except Exception:
    _USE_REDIS_BLACKLIST = False
    _BLACKLISTED_TOKENS_FALLBACK: set = set()


class JWTAuth:
    """JWT Authentication handler with pepper"""
    
    @staticmethod
    def get_jwt_secret() -> str:
        """Get JWT secret key from settings"""
        return getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
    
    @staticmethod
    def get_pepper() -> str:
        """Get pepper from settings"""
        return getattr(settings, 'JWT_PEPPER', 'default-pepper-change-me')
    
    @staticmethod
    def get_expiration_hours() -> int:
        """Get JWT expiration time in hours"""
        return getattr(settings, 'JWT_EXPIRATION_HOURS', 24)
    
    @staticmethod
    def hash_with_pepper(data: str) -> str:
        """Hash data with pepper using HMAC-SHA256"""
        pepper = JWTAuth.get_pepper()
        return hmac.new(
            pepper.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    @staticmethod
    def create_token(user: User) -> str:
        """Create JWT token for user with 24-hour expiration"""
        from game.models import Player
        
        # Get or create player profile
        player, _ = Player.objects.get_or_create(
            user=user,
            defaults={'username': user.username, 'email': user.email}
        )
        
        # Create payload with peppered user ID
        peppered_user_id = JWTAuth.hash_with_pepper(str(user.id))
        
        payload = {
            'user_id': user.id,
            'username': user.username,
            'player_id': player.id,
            'peppered_id': peppered_user_id,
            'is_staff': user.is_staff,       # role hint for the frontend
            'is_superuser': user.is_superuser,
            'exp': datetime.utcnow() + timedelta(hours=JWTAuth.get_expiration_hours()),
            'iat': datetime.utcnow(),
            'jti': str(uuid.uuid4()),   # unique ID ensures each token is distinct
            'type': 'access'
        }
        
        token = jwt.encode(
            payload,
            JWTAuth.get_jwt_secret(),
            algorithm='HS256'
        )
        
        return token
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(
                token,
                JWTAuth.get_jwt_secret(),
                algorithms=['HS256']
            )
            
            # Verify peppered ID
            expected_pepper = JWTAuth.hash_with_pepper(str(payload['user_id']))
            if payload.get('peppered_id') != expected_pepper:
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            # Token expired (after 24 hours)
            return None
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def get_user_from_token(token: str) -> Optional[User]:
        """Get user from JWT token"""
        payload = JWTAuth.verify_token(token)
        if not payload:
            return None
        
        try:
            user = User.objects.get(id=payload['user_id'])
            return user
        except User.DoesNotExist:
            return None
    
    @staticmethod
    def refresh_token(token: str) -> Optional[str]:
        """Refresh token if valid and not expired"""
        payload = JWTAuth.verify_token(token)
        if not payload:
            return None
        
        try:
            user = User.objects.get(id=payload['user_id'])
            return JWTAuth.create_token(user)
        except User.DoesNotExist:
            return None

    @staticmethod
    def add_to_blacklist(token: str, ttl_seconds: int = 172800) -> None:
        """Blacklist a token using Redis (shared across all workers)."""
        if _USE_REDIS_BLACKLIST:
            try:
                _redis_client.setex(f"bl:{token}", ttl_seconds, "1")
                return
            except Exception:
                pass
        _BLACKLISTED_TOKENS_FALLBACK.add(token)

    @staticmethod
    def is_blacklisted(token: str) -> bool:
        """Return True if the token has been explicitly invalidated."""
        if _USE_REDIS_BLACKLIST:
            try:
                return bool(_redis_client.exists(f"bl:{token}"))
            except Exception:
                pass
        return token in _BLACKLISTED_TOKENS_FALLBACK


class JWTAuthMiddleware:
    """Middleware to authenticate requests using JWT"""
    
    @staticmethod
    def authenticate(request):
        """Authenticate request using JWT token"""
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.replace('Bearer ', '')
        user = JWTAuth.get_user_from_token(token)
        
        if user:
            request.user = user
            return user
        
        return None
