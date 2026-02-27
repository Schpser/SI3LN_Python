// search-service.js — Search across players, games, and help content
// ===================================================================

'use strict';

class SearchService {
    constructor(apiFacade) {
        this.api = apiFacade;
        this._debounceTimer = null;
        this._cache = new Map();
        this._cacheMaxAge = 60000; // 1 minute

        // Static searchable content for help & games
        this._helpArticles = [
            { type: 'help', id: 'tutorial-si3ln', title: 'SI3LN Game Tutorial', section: 'games', keywords: ['tutorial', 'how to play', 'controls', 'si3ln', 'space invaders', 'guide'] },
            { type: 'help', id: 'report-player', title: 'Report a Player', section: 'report', keywords: ['report', 'player', 'offensive', 'harassment', 'cheat'] },
            { type: 'help', id: 'report-bug', title: 'Report a Bug', section: 'bug', keywords: ['bug', 'error', 'crash', 'problem', 'issue', 'glitch'] },
            { type: 'help', id: 'support', title: 'Support ARCAD3X', section: 'support', keywords: ['support', 'donate', 'help', 'contribute'] },
        ];

        this._gamesCatalog = [
            { type: 'game', id: 'si3ln', title: 'SI3LN - Space Invaders III Last Night', keywords: ['si3ln', 'space', 'invaders', 'arcade', 'shooter', 'retro'] },
            { type: 'game', id: 'game2', title: 'Space Warriors (Coming Soon)', keywords: ['space', 'warriors', 'coming soon'] },
            { type: 'game', id: 'game3', title: 'Fantasy Quest (Coming Soon)', keywords: ['fantasy', 'quest', 'coming soon'] },
        ];
    }

    /**
     * Perform a unified search across all content types.
     * @param {string} query - Search term
     * @returns {Promise<Array>} Array of search results
     */
    async search(query) {
        if (!query || query.trim().length < (window.APP_CONFIG?.SEARCH_MIN_LENGTH || 2)) {
            return [];
        }

        const q = query.toLowerCase().trim();

        // Check cache
        const cached = this._getFromCache(q);
        if (cached) return cached;

        const results = [];

        // 1. Search static content (games + help) — instant
        results.push(...this._searchStatic(q));

        // 2. Search players via API — async
        try {
            const players = await this._searchPlayers(q);
            results.push(...players);
        } catch (err) {
            if (window.AppLogger) window.AppLogger.warn('Player search failed');
        }

        // Sort: exact matches first, then partial
        results.sort((a, b) => {
            const aExact = a.title.toLowerCase().includes(q) ? 0 : 1;
            const bExact = b.title.toLowerCase().includes(q) ? 0 : 1;
            return aExact - bExact;
        });

        // Limit results
        const limited = results.slice(0, window.APP_CONFIG?.SEARCH_MAX_RESULTS || 20);
        
        this._setCache(q, limited);
        return limited;
    }

    /**
     * Search static content (games catalog + help articles)
     */
    _searchStatic(query) {
        const results = [];

        for (const game of this._gamesCatalog) {
            if (this._matches(game, query)) {
                results.push({
                    type: 'game',
                    id: game.id,
                    title: game.title,
                    icon: '🎮',
                    action: game.id === 'si3ln' ? 'launch-game' : null,
                    description: game.id === 'si3ln' ? 'Click to play' : 'Coming soon',
                });
            }
        }

        for (const article of this._helpArticles) {
            if (this._matches(article, query)) {
                results.push({
                    type: 'help',
                    id: article.id,
                    title: article.title,
                    icon: '❓',
                    action: 'show-help',
                    section: article.section,
                    description: 'Help article',
                });
            }
        }

        return results;
    }

    /**
     * Search players via API
     */
    async _searchPlayers(query) {
        const players = await this.api.listPlayers();
        if (!Array.isArray(players)) return [];

        return players
            .filter(p => {
                const name = (p.username || '').toLowerCase();
                return name.includes(query);
            })
            .slice(0, 10)
            .map(p => ({
                type: 'player',
                id: p.id,
                title: p.username,
                icon: '👤',
                action: 'show-profile',
                description: `Player${p.total_score ? ' — ' + p.total_score + ' pts' : ''}`,
            }));
    }

    _matches(item, query) {
        const titleMatch = item.title.toLowerCase().includes(query);
        const keywordMatch = item.keywords.some(kw => kw.includes(query) || query.includes(kw));
        return titleMatch || keywordMatch;
    }

    // ── Debounced search for live input ───────────────────────────

    debounceSearch(query, callback) {
        clearTimeout(this._debounceTimer);
        this._debounceTimer = setTimeout(async () => {
            const results = await this.search(query);
            callback(results);
        }, window.APP_CONFIG?.SEARCH_DEBOUNCE_MS || 300);
    }

    // ── Simple cache ──────────────────────────────────────────────

    _getFromCache(key) {
        const entry = this._cache.get(key);
        if (!entry) return null;
        if (Date.now() - entry.time > this._cacheMaxAge) {
            this._cache.delete(key);
            return null;
        }
        return entry.data;
    }

    _setCache(key, data) {
        this._cache.set(key, { data, time: Date.now() });
        // Evict old entries if cache gets too big
        if (this._cache.size > 100) {
            const oldest = this._cache.keys().next().value;
            this._cache.delete(oldest);
        }
    }
}

window.SearchService = SearchService;
