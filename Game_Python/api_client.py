"""
REST API client for SI3LN Python game.

Desktop mode  : uses `requests` (sync HTTP)
Browser/Pygbag: requests is unavailable; API calls silently return None
                (scores/sessions are disabled in browser – they go through the
                 frontend JS layer instead)
"""

import os
import sys
import json
import base64

# ── Browser detection ─────────────────────────────────────────────────────────
# Pygbag sets sys.platform = 'emscripten' when running in the browser
IS_BROWSER = sys.platform in ("emscripten", "wasi")

# ── requests import (desktop only) ───────────────────────────────────────────
if not IS_BROWSER:
    try:
        import requests as _requests
        _HAS_REQUESTS = True
    except ImportError:
        _HAS_REQUESTS = False
else:
    _HAS_REQUESTS = False

# ── Config ────────────────────────────────────────────────────────────────────
try:
    from constants import API_URL, API_TOKEN
except ImportError:
    API_URL   = os.environ.get("SI3LN_API_URL", "http://localhost:8000")
    API_TOKEN = os.environ.get("SI3LN_TOKEN", "")


def _jwt_field(token: str, field: str):
    """Decode a single field from a JWT payload without verification."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        payload = parts[1]
        payload += "=" * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(payload).decode())
        return data.get(field)
    except Exception:
        return None


class APIClient:
    """Thin wrapper around the SI3LN Django-Ninja REST API."""

    def __init__(self):
        self._token: str = ""
        self._player_id: int | None = None
        self._username: str = ""
        self._session_id: int | None = None
        self._load_token()

    # ── Token management ──────────────────────────────────────────────────────

    def _load_token(self):
        """Load JWT from env var (desktop) or window.SI3LN_JWT_TOKEN (browser)."""
        token = API_TOKEN or os.environ.get("SI3LN_TOKEN", "")

        if not token and IS_BROWSER:
            try:
                import platform
                token = getattr(platform.window, "SI3LN_JWT_TOKEN", "") or ""
            except Exception:
                token = ""

        if token:
            self.set_token(token)

    def set_token(self, token: str):
        self._token  = token
        self._player_id = _jwt_field(token, "player_id")
        self._username  = _jwt_field(token, "username") or ""

    def is_authenticated(self) -> bool:
        return bool(self._token and self._player_id)

    def get_username(self) -> str:
        return self._username

    def get_player_id(self):
        return self._player_id

    # ── HTTP helpers ──────────────────────────────────────────────────────────

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self._token:
            h["Authorization"] = f"Bearer {self._token}"
        return h

    def _get(self, path: str):
        if not _HAS_REQUESTS:
            return None
        try:
            r = _requests.get(
                f"{API_URL}{path}", headers=self._headers(), timeout=5
            )
            return r.json() if r.ok else None
        except Exception:
            return None

    def _post(self, path: str, data: dict):
        if not _HAS_REQUESTS:
            return None
        try:
            r = _requests.post(
                f"{API_URL}{path}", json=data, headers=self._headers(), timeout=5
            )
            return r.json() if r.ok else None
        except Exception:
            return None

    def _patch(self, path: str, data: dict):
        if not _HAS_REQUESTS:
            return None
        try:
            r = _requests.patch(
                f"{API_URL}{path}", json=data, headers=self._headers(), timeout=5
            )
            return r.json() if r.ok else None
        except Exception:
            return None

    # ── Public API ────────────────────────────────────────────────────────────

    def login(self, username: str, password: str) -> bool:
        """Authenticate and store JWT. Returns True on success."""
        result = self._post("/api/auth/login", {
            "username": username,
            "password": password,
        })
        if result and "access_token" in result:
            self.set_token(result["access_token"])
            return True
        return False

    def start_session(self, world_id: int = 1) -> int | None:
        """Start a game session. Returns session id or None."""
        if not self.is_authenticated():
            return None
        result = self._post("/api/game/sessions", {
            "world_id":  world_id,
            "player_id": self._player_id,
        })
        if result and "id" in result:
            self._session_id = result["id"]
            return self._session_id
        return None

    def end_session(
        self,
        score: int = 0,
        level: int = 1,
        enemies_killed: int = 0,
        duration: int = 0,
    ):
        """End the current session with results. Returns response or None."""
        if not self.is_authenticated() or not self._session_id:
            return None
        result = self._patch(f"/api/game/sessions/{self._session_id}", {
            "score":          score,
            "level_reached":  level,
            "enemies_killed": enemies_killed,
            "duration":       duration,
            "completed":      True,
        })
        self._session_id = None
        return result

    def get_leaderboard(self, limit: int = 10) -> list:
        """Return list of top scores. Falls back to empty list on error."""
        result = self._get(f"/api/game/leaderboard?limit={limit}")
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and "results" in result:
            return result["results"]
        return []

    def get_player(self) -> dict | None:
        """Return player profile dict or None."""
        if not self._player_id:
            return None
        return self._get(f"/api/game/players/{self._player_id}")


# ── Singleton ─────────────────────────────────────────────────────────────────
api_client = APIClient()
