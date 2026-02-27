// config.js — Application configuration & version
// ================================================
// Single source of truth for app-wide constants.
// Loaded BEFORE all other JS files.

'use strict';

window.APP_CONFIG = Object.freeze({
    // ── Version ─────────────────────────────────────────────
    VERSION: '2.0.0',
    BUILD_DATE: '2026-02-27',
    APP_NAME: 'ARCAD3X',
    
    // ── API ─────────────────────────────────────────────────
    API_BASE_URL: '/api',
    
    // ── Security ────────────────────────────────────────────
    // In production, set to false to suppress ALL console output
    DEBUG_MODE: false,
    LOG_API_CALLS: false,
    LOG_TOKENS: false,   // NEVER set to true in production
    
    // ── Token storage key (single point of change) ──────────
    TOKEN_KEY: 'SI3LN_SESSION',
    LEGACY_TOKEN_KEY: 'access_token',   // kept for migration
    
    // ── Game settings ───────────────────────────────────────
    GAME_LOAD_TIMEOUT: 30000,   // ms before we show a timeout warning
    GAME_IFRAME_SANDBOX: 'allow-scripts allow-same-origin allow-popups allow-forms',
    
    // ── Search ──────────────────────────────────────────────
    SEARCH_MIN_LENGTH: 2,
    SEARCH_DEBOUNCE_MS: 300,
    SEARCH_MAX_RESULTS: 20,
    
    // ── i18n ────────────────────────────────────────────────
    DEFAULT_LANGUAGE: 'en',
    SUPPORTED_LANGUAGES: ['en', 'fr'],
});

// Safe logger — only outputs when DEBUG_MODE is true
window.AppLogger = {
    _enabled: window.APP_CONFIG.DEBUG_MODE,
    
    log(...args)   { if (this._enabled) console.log('[ARCAD3X]', ...args); },
    warn(...args)  { if (this._enabled) console.warn('[ARCAD3X]', ...args); },
    error(...args) { console.error('[ARCAD3X]', ...args); },  // errors always logged
    
    // Explicitly separate: NEVER logs tokens/secrets even in debug mode
    api(method, url, status) {
        if (window.APP_CONFIG.LOG_API_CALLS) {
            console.log(`[API] ${method} ${url} → ${status}`);
        }
    },
};
