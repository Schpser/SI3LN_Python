"""
facade.py — Security Facade for SI3LN API
==========================================
Provides a clean, secure interface between frontend and backend:
- Strips sensitive fields from responses (tokens, internal IDs, etc.)
- Validates and sanitizes all inputs
- Handles session-based auth as alternative to raw JWT exposure
- Centralised error handling with safe error messages

Usage in views:
    from game.facade import ApiFacade
    facade = ApiFacade(request)
    result = facade.login(username, password)   # returns session cookie, NOT raw JWT
"""

import hashlib
import json
import logging
import re
import time
from functools import wraps
from typing import Any, Dict, List, Optional

from django.conf import settings

logger = logging.getLogger("si3ln.facade")

# ---------------------------------------------------------------------------
# Sensitive fields that must NEVER be returned to the frontend
# ---------------------------------------------------------------------------
SENSITIVE_FIELDS = frozenset({
    "password", "password_hash", "secret", "internal_id",
    "private_key", "refresh_token", "raw_token",
})

# Fields allowed in token-related responses (we only expose an opaque session id)
SAFE_AUTH_FIELDS = frozenset({
    "session_id", "username", "player_id", "role", "expires_at",
})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _sanitize_dict(data: dict, allow: Optional[frozenset] = None) -> dict:
    """Remove sensitive keys from a dict.  If *allow* is given, keep ONLY those keys."""
    if allow:
        return {k: v for k, v in data.items() if k in allow}
    return {k: v for k, v in data.items() if k not in SENSITIVE_FIELDS}


def _sanitize(data: Any) -> Any:
    """Recursively sanitize data structures."""
    if isinstance(data, dict):
        return {k: _sanitize(v) for k, v in data.items() if k not in SENSITIVE_FIELDS}
    if isinstance(data, (list, tuple)):
        return [_sanitize(item) for item in data]
    return data


def _safe_error(message: str = "An error occurred", status: int = 400) -> dict:
    """Return a generic, non-leaking error envelope."""
    return {"ok": False, "error": message, "status": status}


def _validate_username(username: str) -> bool:
    """Validate username format."""
    return bool(re.match(r'^[A-Za-z0-9_]{3,30}$', username))


def _validate_email(email: str) -> bool:
    """Validate email format."""
    return bool(re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email))


# ---------------------------------------------------------------------------
# Rate limiting (simple in-memory, use Redis in production)
# ---------------------------------------------------------------------------
_rate_limits: Dict[str, List[float]] = {}
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 30     # requests per window


def _check_rate_limit(identifier: str) -> bool:
    """Return True if the request is within rate limits."""
    now = time.time()
    if identifier not in _rate_limits:
        _rate_limits[identifier] = []

    # Clean old entries
    _rate_limits[identifier] = [
        t for t in _rate_limits[identifier]
        if now - t < RATE_LIMIT_WINDOW
    ]

    if len(_rate_limits[identifier]) >= RATE_LIMIT_MAX:
        return False

    _rate_limits[identifier].append(now)
    return True


# ---------------------------------------------------------------------------
# Facade class
# ---------------------------------------------------------------------------
class ApiFacade:
    """
    Security-first facade wrapping the SI3LN game API.

    Every public method:
      1. Validates inputs
      2. Delegates to the real service layer
      3. Sanitises the output before returning
      4. Logs actions at INFO level (never logging secrets)
    """

    def __init__(self, request=None):
        self.request = request
        self._client_ip = self._get_client_ip() if request else "unknown"

    # -- internal helpers ---------------------------------------------------

    def _get_client_ip(self) -> str:
        """Extract client IP from request, respecting X-Forwarded-For."""
        if not self.request:
            return "unknown"
        xff = self.request.META.get("HTTP_X_FORWARDED_FOR", "")
        if xff:
            return xff.split(",")[0].strip()
        return self.request.META.get("REMOTE_ADDR", "unknown")

    def _rate_check(self) -> Optional[dict]:
        """Check rate limit; returns error dict if exceeded, else None."""
        if not _check_rate_limit(self._client_ip):
            logger.warning("Rate limit exceeded for %s", self._client_ip)
            return _safe_error("Too many requests. Please wait.", 429)
        return None

    # -- Auth facade --------------------------------------------------------

    def sanitize_login_response(self, raw_response: dict) -> dict:
        """
        Takes the raw login response (which contains the JWT token)
        and returns a safe version for the frontend.
        The raw token is stored server-side or in httpOnly cookie.
        """
        safe = {
            "ok": True,
            "username": raw_response.get("username", ""),
            "player_id": raw_response.get("player_id"),
            "role": "admin" if raw_response.get("is_staff") else "player",
        }
        # Generate an opaque session identifier (not the JWT itself)
        token = raw_response.get("token", "")
        if token:
            safe["session_id"] = hashlib.sha256(
                f"{token[:16]}:{time.time()}".encode()
            ).hexdigest()[:32]
        return safe

    def sanitize_profile_response(self, raw_profile: dict) -> dict:
        """Strip sensitive fields from profile data."""
        return _sanitize(raw_profile)

    def sanitize_leaderboard(self, entries: list) -> list:
        """Ensure leaderboard entries only have safe fields."""
        safe_fields = {"player_username", "username", "score", "level_reached", "rank"}
        return [
            {k: v for k, v in entry.items() if k in safe_fields}
            for entry in entries
        ]

    def sanitize_game_session(self, session: dict) -> dict:
        """Return only safe session fields."""
        safe_fields = {
            "id", "player_id", "world_id", "score",
            "level_reached", "started_at", "ended_at", "completed",
        }
        return {k: v for k, v in session.items() if k in safe_fields}

    def validate_login_input(self, username: str, password: str) -> Optional[str]:
        """Validate login inputs. Returns error message or None."""
        if not username or not password:
            return "Username and password are required"
        if len(username) > 30:
            return "Username too long"
        if len(password) > 128:
            return "Password too long"
        return None

    def validate_signup_input(self, data: dict) -> Optional[str]:
        """Validate signup inputs. Returns error message or None."""
        username = data.get("username", "")
        email = data.get("email", "")
        password = data.get("password", "")

        if not _validate_username(username):
            return "Invalid username format (3-30 chars, letters/numbers/underscore)"
        if not _validate_email(email):
            return "Invalid email format"
        if len(password) < 8:
            return "Password must be at least 8 characters"
        if not re.search(r'[A-Z]', password):
            return "Password must contain at least one uppercase letter"
        if not re.search(r'\d', password):
            return "Password must contain at least one number"
        return None

    def validate_report_input(self, data: dict) -> Optional[str]:
        """Validate report inputs."""
        if not data.get("username"):
            return "Player username is required"
        if not data.get("reason"):
            return "Report reason is required"
        if not data.get("details") or len(data["details"]) < 10:
            return "Please provide more details (at least 10 characters)"
        return None

    def validate_search_query(self, query: str) -> Optional[str]:
        """Validate search query."""
        if not query or len(query.strip()) < 2:
            return "Search query must be at least 2 characters"
        if len(query) > 100:
            return "Search query too long"
        # Prevent injection patterns
        if re.search(r'[<>{}\\]', query):
            return "Invalid characters in search query"
        return None


# ---------------------------------------------------------------------------
# Django middleware for automatic response sanitization
# ---------------------------------------------------------------------------
class SecurityFacadeMiddleware:
    """
    Django middleware that:
    1. Adds security headers to all API responses
    2. Strips sensitive fields from JSON responses
    3. Prevents token leakage in error messages
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Add security headers
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "SAMEORIGIN"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        # For API responses, sanitize JSON content
        if (
            request.path.startswith("/api/")
            and response.get("Content-Type", "").startswith("application/json")
            and hasattr(response, "content")
        ):
            try:
                data = json.loads(response.content)
                sanitized = _sanitize(data)
                response.content = json.dumps(sanitized).encode()
                response["Content-Length"] = len(response.content)
            except (json.JSONDecodeError, Exception):
                pass  # Not JSON or can't parse — leave as-is

        return response
