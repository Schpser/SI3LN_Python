class APIClient {
    constructor(baseURL = '/api') {
        this.baseURL = baseURL;
        console.log('API Client initialized with baseURL:', this.baseURL);
    }

    async request(endpoint, options = {}) {
        const token = localStorage.getItem('access_token');
        const fullURL = `${this.baseURL}${endpoint}`;
        
        console.log('API Request:', fullURL, options.method || 'GET');

        const headers = {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
            ...options.headers
        };

        try {
            const response = await fetch(fullURL, {        
                ...options,
                headers
            });

            console.log('API Response:', response.status, response.statusText);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('API Error Response:', errorText);
                throw new Error(`API Error: ${response.status} - ${errorText}`);
            }

            const data = await response.json();
            console.log('API Success:', data);
            return data;
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }

    // Auth
    async login(username, password) {
        return this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
    }

    async signup(userData) {
        console.log('Signup called with:', userData);
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
    }

    // Player/Profile endpoints
    async getCurrentPlayer() {
        // Prefer the enriched /game/profile/me endpoint (includes achievements, recent scores)
        try {
            return await this.request('/game/profile/me');
        } catch (_) {
            // Fallback: decode player_id from JWT and call /game/players/:id
            const token = localStorage.getItem('access_token');
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
            body: JSON.stringify(data)
        });
    }

    async listPlayers() {
        return this.request('/game/players');
    }

    async getLeaderboard(limit = 10) {
        return this.request(`/game/leaderboard?limit=${limit}`);
    }

    // Current authenticated user info (calls /auth/me)
    async getCurrentUser() {
        return this.request('/auth/me');
    }

    async getStats() {
        return this.request('/game/stats');
    }

    // ── Role helpers ─────────────────────────────────────────────────────────

    /**
     * Decode the JWT stored in localStorage and return a role string.
     * Returns: 'admin' | 'player' | 'guest'
     * (No network call – reads the JWT payload directly.)
     */
    getLocalRole() {
        const token = localStorage.getItem('access_token');
        if (!token) return 'guest';
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            if (payload.is_superuser || payload.is_staff) return 'admin';
            return 'player';
        } catch (_) {
            return 'guest';
        }
    }

    /** Decode the player_id from the stored JWT token. */
    getLocalPlayerId() {
        const token = localStorage.getItem('access_token');
        if (!token) return null;
        try {
            return JSON.parse(atob(token.split('.')[1])).player_id ?? null;
        } catch (_) { return null; }
    }

    /** Decode the username from the stored JWT token. */
    getLocalUsername() {
        const token = localStorage.getItem('access_token');
        if (!token) return null;
        try {
            return JSON.parse(atob(token.split('.')[1])).username ?? null;
        } catch (_) { return null; }
    }

    // Game Sessions (for C++ game engine integration)
    async createGameSession(playerId, worldId = 1) {
        return this.request('/game/sessions', {
            method: 'POST',
            body: JSON.stringify({
                player_id: playerId,
                world_id: worldId
            })
        });
    }

    async updateGameSession(sessionId, score, level) {
        return this.request(`/game/sessions/${sessionId}`, {
            method: 'PATCH',
            body: JSON.stringify({
                score: score,
                level_reached: level
            })
        });
    }

    async endGameSession(sessionId, finalScore, finalLevel) {
        return this.request(`/game/sessions/${sessionId}`, {
            method: 'PATCH',
            body: JSON.stringify({
                score: finalScore,
                level_reached: finalLevel,
                completed: true          // triggers Player.total_score update on the server
            })
        });
    }

    async getGameSessions(playerId = null) {
        const params = playerId ? `?player_id=${playerId}` : '';
        return this.request(`/game/sessions${params}`);
    }
}

window.api = new APIClient();
console.log('API Client ready:', window.api);
