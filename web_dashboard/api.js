// api.js — Raw API Client (internal — app code should use window.facade)
// =======================================================================
// SECURITY: No console.log of tokens, response bodies, or sensitive data.
// All logging goes through AppLogger which respects APP_CONFIG.DEBUG_MODE.

'use strict';

class APIClient {
    constructor(baseURL) {
        this.baseURL = baseURL || (window.APP_CONFIG ? window.APP_CONFIG.API_BASE_URL : '/api');
    }

    _getToken() {
        return localStorage.getItem(
            (window.APP_CONFIG && window.APP_CONFIG.TOKEN_KEY) || 'SI3LN_SESSION'
        ) || localStorage.getItem('access_token');
    }

    async request(endpoint, options = {}) {
        const token = this._getToken();
        const fullURL = `${this.baseURL}${endpoint}`;

        const headers = {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
            ...options.headers,
        };

        try {
            const response = await fetch(fullURL, { ...options, headers });

            // Safe logging — method + endpoint + status only
            if (window.AppLogger) {
                window.AppLogger.api(options.method || 'GET', endpoint, response.status);
            }

            if (!response.ok) {
                await response.text(); // consume body
                throw new Error(`API Error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            if (window.AppLogger) window.AppLogger.error('Request failed:', endpoint);
            throw error;
        }
    }

    async login(username, password) {
        return this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password }),
        });
    }

    async signup(userData) {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData),
        });
    }

    async getCurrentPlayer() {
        try {
            return await this.request('/game/profile/me');
        } catch (_) {
            const token = this._getToken();
            if (!token) throw new Error('Not authenticated');
            const payload = JSON.parse(atob(token.split('.')[1]));
            return this.getPlayer(payload.player_id);
        }
    }

    async getPlayer(playerId) {
        return this.request(`/game/players/${playerId}`);
    }

    async updatePlayer(playerId, data) {
        return this.request(`/game/players/${playerId}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async listPlayers() {
        return this.request('/game/players');
    }

    async getLeaderboard(limit = 10) {
        return this.request(`/game/leaderboard?limit=${limit}`);
    }

    async getCurrentUser() {
        return this.request('/auth/me');
    }

    async getStats() {
        return this.request('/game/stats');
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

    async createGameSession(playerId, worldId = null) {
        const body = { player_id: playerId };
        if (worldId) body.world_id = worldId;
        return this.request('/game/sessions', {
            method: 'POST',
            body: JSON.stringify(body),
        });
    }

    async updateGameSession(sessionId, score, level) {
        return this.request(`/game/sessions/${sessionId}`, {
            method: 'PATCH',
            body: JSON.stringify({ score, level_reached: level }),
        });
    }

    async endGameSession(sessionId, finalScore, finalLevel) {
        return this.request(`/game/sessions/${sessionId}`, {
            method: 'PATCH',
            body: JSON.stringify({
                score: finalScore,
                level_reached: finalLevel,
                completed: true,
            }),
        });
    }

    async getGameSessions(playerId = null) {
        const params = playerId ? `?player_id=${playerId}` : '';
        return this.request(`/game/sessions${params}`);
    }
}

// Create raw client (internal — app code should use window.facade)
window._rawApiClient = new APIClient();
window.api = window._rawApiClient;
