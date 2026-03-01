// api-facade.js — Secure API Facade Service
// ============================================
// Wraps all API calls through a security-first facade:
// - NO console.log of tokens, secrets, or full responses
// - Input validation before sending requests
// - Response sanitization before returning to callers
// - Centralised error handling
//
// This replaces direct usage of the raw APIClient.

'use strict';

class ApiFacadeService {
    constructor(rawClient) {
        this._raw = rawClient;
    }

    // ── Auth ──────────────────────────────────────────────────────

    async login(username, password) {
        if (!username || !password) throw new Error('Username and password are required');
        
        const result = await this._raw.login(username, password);
        
        // Store token securely (no logging)
        if (result.token) {
            this._storeToken(result.token);
        }
        
        // Return only safe fields — token is NOT returned to caller
        return {
            ok: true,
            username: result.username || username,
            player_id: result.player_id,
        };
    }

    async signup(userData) {
        // Validate before sending
        const errors = this._validateSignup(userData);
        if (errors) throw new Error(errors);
        
        const result = await this._raw.signup(userData);
        
        if (result.token) {
            this._storeToken(result.token);
        }
        
        return {
            ok: true,
            username: result.username || userData.username,
            player_id: result.player_id,
        };
    }

    logout() {
        localStorage.removeItem(window.APP_CONFIG.TOKEN_KEY);
        localStorage.removeItem(window.APP_CONFIG.LEGACY_TOKEN_KEY);
        localStorage.removeItem('SI3LN_JWT_TOKEN');
    }

    // ── Profile ───────────────────────────────────────────────────

    async getCurrentPlayer() {
        return this._sanitize(await this._raw.getCurrentPlayer());
    }

    async getPlayer(playerId) {
        return this._sanitize(await this._raw.getPlayer(playerId));
    }

    async updatePlayer(playerId, data) {
        return this._sanitize(await this._raw.updatePlayer(playerId, data));
    }

    async updateProfile(data) {
        return this._sanitize(
            await this._raw.request('/game/profile/me', {
                method: 'PATCH',
                body: JSON.stringify(data),
            })
        );
    }

    async uploadAvatar(file) {
        const token = this._getToken();
        const formData = new FormData();
        formData.append('avatar', file);
        
        const response = await fetch('/api/game/profile/me/avatar', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData,
        });
        
        if (!response.ok) throw new Error('Avatar upload failed');
        return response.json();
    }

    // ── Leaderboard ───────────────────────────────────────────────

    async getLeaderboard(limit = 10) {
        const data = await this._raw.getLeaderboard(limit);
        // Only return safe leaderboard fields
        if (Array.isArray(data)) {
            return data.map(entry => ({
                player_username: entry.player_username,
                score: entry.score,
                level_reached: entry.level_reached,
            }));
        }
        return data;
    }

    // ── Game Sessions ─────────────────────────────────────────────

    async createGameSession(worldId = null) {
        const playerId = this.getLocalPlayerId();
        if (!playerId) throw new Error('Not authenticated');
        
        const body = { player_id: playerId };
        if (worldId) body.world_id = worldId;
        
        const result = await this._raw.request('/game/sessions', {
            method: 'POST',
            body: JSON.stringify(body),
        });
        
        return this._sanitizeSession(result);
    }

    async endGameSession(sessionId, score, level) {
        return this._sanitizeSession(
            await this._raw.request(`/game/sessions/${sessionId}`, {
                method: 'PATCH',
                body: JSON.stringify({
                    score,
                    level_reached: level,
                    completed: true,
                }),
            })
        );
    }

    async getGameSessions(playerId = null) {
        const params = playerId ? `?player_id=${playerId}` : '';
        const data = await this._raw.request(`/game/sessions${params}`);
        return Array.isArray(data) ? data.map(s => this._sanitizeSession(s)) : data;
    }

    // ── Stats ─────────────────────────────────────────────────────

    async getStats() {
        return this._raw.getStats();
    }

    // ── Players (for search) ──────────────────────────────────────

    async listPlayers() {
        const data = await this._raw.listPlayers();
        return Array.isArray(data) ? data.map(p => this._sanitize(p)) : data;
    }

    // ── Token helpers (private — never expose raw token) ──────────

    _storeToken(token) {
        // Store under the new key
        localStorage.setItem(window.APP_CONFIG.TOKEN_KEY, token);
        // Also keep legacy key for backward compat with game iframe
        localStorage.setItem(window.APP_CONFIG.LEGACY_TOKEN_KEY, token);
    }

    _getToken() {
        return localStorage.getItem(window.APP_CONFIG.TOKEN_KEY)
            || localStorage.getItem(window.APP_CONFIG.LEGACY_TOKEN_KEY);
    }

    isAuthenticated() {
        return !!this._getToken();
    }

    getLocalRole() {
        const token = this._getToken();
        if (!token) return 'guest';
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            if (payload.is_superuser || payload.is_staff) return 'admin';
            return 'player';
        } catch (_) { return 'guest'; }
    }

    getLocalPlayerId() {
        const token = this._getToken();
        if (!token) return null;
        try {
            return JSON.parse(atob(token.split('.')[1])).player_id ?? null;
        } catch (_) { return null; }
    }

    getLocalUsername() {
        const token = this._getToken();
        if (!token) return null;
        try {
            return JSON.parse(atob(token.split('.')[1])).username ?? null;
        } catch (_) { return null; }
    }

    // ── Sanitization (private) ────────────────────────────────────

    _sanitize(data) {
        if (!data || typeof data !== 'object') return data;
        const BLOCKED = new Set([
            'password', 'password_hash', 'secret', 'private_key',
            'refresh_token', 'raw_token', 'token',
        ]);
        const out = {};
        for (const [k, v] of Object.entries(data)) {
            if (BLOCKED.has(k)) continue;
            out[k] = (typeof v === 'object' && v !== null) ? this._sanitize(v) : v;
        }
        return out;
    }

    _sanitizeSession(session) {
        if (!session) return session;
        return {
            id: session.id,
            player_id: session.player_id,
            world_id: session.world_id,
            score: session.score,
            level_reached: session.level_reached,
            started_at: session.started_at,
            ended_at: session.ended_at,
            completed: session.completed,
        };
    }

    _validateSignup(data) {
        if (!data.username || !/^[A-Za-z0-9_]{3,30}$/.test(data.username)) {
            return 'Invalid username (3-30 chars, letters/numbers/underscore)';
        }
        if (!data.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
            return 'Invalid email format';
        }
        if (!data.password || data.password.length < 8) {
            return 'Password must be at least 8 characters';
        }
        return null;
    }
}

// Export globally
window.ApiFacadeService = ApiFacadeService;
