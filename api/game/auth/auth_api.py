import re
import time
import hashlib
from collections import defaultdict

from ninja import Router, Schema
from ninja.responses import Response
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .jwt_auth import JWTAuth
from .auth_decorators import jwt_auth
from game.schemas import ChangePasswordSchema, AccountUpdateSchema

router = Router()

# ── Simple in-memory rate limiter ──────────────────────────────────────────
_rate_store: dict[str, list[float]] = defaultdict(list)

RATE_LIMITS = {
    "auth": {"requests": 30, "window": 60},       # 30 req / 60 s for login/register
    "password": {"requests": 5, "window": 60},     # 5  req / 60 s for password change
}


def _rate_limited(bucket: str, key: str) -> bool:
    """Return True if the caller has exceeded the rate limit."""
    cfg = RATE_LIMITS.get(bucket, RATE_LIMITS["auth"])
    now = time.time()
    window = cfg["window"]
    store_key = f"{bucket}:{key}"
    # Prune old entries
    _rate_store[store_key] = [t for t in _rate_store[store_key] if now - t < window]
    if len(_rate_store[store_key]) >= cfg["requests"]:
        return True
    _rate_store[store_key].append(now)
    return False


def _get_client_ip(request) -> str:
    """Extract client IP from request (supports X-Forwarded-For)."""
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _validate_email_format(email: str) -> bool:
    """Basic RFC-style email validation."""
    if not email:
        return True  # empty is allowed (optional field)
    return bool(re.match(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', email))


def _validate_password_strength(password: str) -> list[str]:
    """Validate password using Django's built-in validators + custom checks."""
    errors: list[str] = []
    if not password:
        errors.append("Password cannot be empty.")
        return errors
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    try:
        validate_password(password)
    except DjangoValidationError as e:
        errors.extend(e.messages)
    return errors


class LoginSchema(Schema):
    username: str
    password: str


class RegisterSchema(Schema):
    username: str
    password: str
    email: str = ""


class TokenSchema(Schema):
    token: str
    username: str
    player_id: int


@router.post("/register", response=TokenSchema, tags=["Auth"])
def register(request, payload: RegisterSchema):
    """Register a new user"""
    from game.models import Player

    # ── Rate limit ──
    ip = _get_client_ip(request)
    if _rate_limited("auth", ip):
        return Response(
            {"error": "Too many requests. Please try again later."},
            status=429,
            headers={"Retry-After": "60"},
        )

    # ── Validate password ──
    pwd_errors = _validate_password_strength(payload.password)
    if pwd_errors:
        return Response({"error": "Password too weak.", "details": pwd_errors}, status=400)

    # ── Validate email format ──
    if not _validate_email_format(payload.email):
        return Response({"error": "Invalid email format."}, status=400)

    # Check if user exists
    if User.objects.filter(username=payload.username).exists():
        return Response({"error": "Username already exists"}, status=400)
    
    # Create user
    user = User.objects.create_user(
        username=payload.username,
        password=payload.password,
        email=payload.email
    )
    
    # Create player profile
    player = Player.objects.create(
        user=user,
        username=payload.username
    )
    
    # Generate JWT token (expires in 24 hours)
    token = JWTAuth.create_token(user)
    
    return {
        "token": token,
        "username": user.username,
        "player_id": player.id
    }


@router.post("/login", response=TokenSchema, tags=["Auth"])
def login(request, payload: LoginSchema):
    """Login user and get JWT token (valid for 24 hours)"""
    from game.models import Player

    # ── Rate limit ──
    ip = _get_client_ip(request)
    if _rate_limited("auth", ip):
        return Response(
            {"error": "Too many requests. Please try again later."},
            status=429,
            headers={"Retry-After": "60"},
        )

    # Constant-time authentication: always hash even if user doesn't exist
    # to prevent timing-based username enumeration.
    user = authenticate(username=payload.username, password=payload.password)
    
    if user is None:
        return Response({"error": "Invalid credentials"}, status=401)
    
    # Get or create player profile
    player, _ = Player.objects.get_or_create(
        user=user,
        defaults={'username': user.username, 'email': user.email or None}
    )
    
    # Generate JWT token (expires in 24 hours)
    token = JWTAuth.create_token(user)
    
    return {
        "token": token,
        "username": user.username,
        "player_id": player.id
    }


@router.post("/logout", tags=["Auth"])
def logout(request):
    """Logout user (client should discard token)"""
    # JWT is stateless, so we just return success
    # Client should discard the token
    return {"message": "Logged out successfully. Please discard your token."}


@router.post("/refresh", response=TokenSchema, tags=["Auth"], auth=jwt_auth)
def refresh_token(request):
    """Refresh JWT token (extends expiration by 24 hours)"""
    from game.models import Player
    
    # Get the token from the authenticated request
    auth_header = request.headers.get('Authorization', '')
    token = auth_header[7:] if auth_header.startswith('Bearer ') else None
    
    if not token:
        return Response({"error": "No token provided"}, status=401)
    
    new_token = JWTAuth.refresh_token(token)
    
    if not new_token:
        return Response({"error": "Invalid or expired token"}, status=401)
    
    # Get user info
    user = request.auth
    player = Player.objects.get(user=user)
    
    return {
        "token": new_token,
        "username": user.username,
        "player_id": player.id
    }


@router.get("/me", tags=["Auth"], auth=jwt_auth)
def get_current_user(request):
    """Get current authenticated user info (requires Bearer token)"""
    user = request.auth  # User is already set by jwt_auth
    
    if not user:
        return Response({"error": "Invalid or expired token. Please login again."}, status=401)
    
    from game.models import Player
    player = Player.objects.get(user=user)
    
    role = "admin" if user.is_superuser else ("staff" if user.is_staff else "player")
    return {
        "username": user.username,
        "email": user.email,
        "player_id": player.id,
        "total_score": player.total_score,
        "games_played": player.games_played,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
        "role": role,
    }


@router.post("/change-password", tags=["Auth"], auth=jwt_auth)
def change_password(request, payload: ChangePasswordSchema):
    """Change password for authenticated user"""
    user = request.auth

    # ── Rate limit ──
    ip = _get_client_ip(request)
    if _rate_limited("password", ip):
        return Response(
            {"error": "Too many requests. Please try again later."},
            status=429,
            headers={"Retry-After": "60"},
        )
    
    # Verify old password
    if not user.check_password(payload.old_password):
        return Response({"error": "Current password is incorrect"}, status=400)

    # ── Validate new password strength ──
    pwd_errors = _validate_password_strength(payload.new_password)
    if pwd_errors:
        return Response({"error": "New password too weak.", "details": pwd_errors}, status=400)
    
    # Set new password
    user.set_password(payload.new_password)
    user.save()
    
    return {"message": "Password changed successfully"}


@router.patch("/update-account", tags=["Auth"], auth=jwt_auth)
def update_account(request, payload: AccountUpdateSchema):
    """Update account email and name for authenticated user"""
    from game.models import Player
    
    user = request.auth
    
    # Update user fields if provided
    if payload.email is not None:
        user.email = payload.email
        # Also update player email
        try:
            player = Player.objects.get(user=user)
            player.email = payload.email or None
            player.save()
        except Player.DoesNotExist:
            pass
    
    if payload.first_name is not None:
        user.first_name = payload.first_name
    
    if payload.last_name is not None:
        user.last_name = payload.last_name
    
    user.save()
    
    return {
        "message": "Account updated successfully",
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }
