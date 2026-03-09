/**
 * SI3LN Mobile – Main entry point
 *
 * This runs ONLY on the mobile version (/mobile/).
 *
 * Shared modules available (served from /js/ with immutable cache):
 *   - window.API_CONFIG  → from /js/config.js
 *   - window.i18n        → from /js/i18n.js  (if exported globally)
 *   - ApiFacade          → from /js/services/api-facade.js
 *
 * ─────────────────────────────────────────────────────────────────────────
 */

(function () {
    'use strict';

    const app = document.getElementById('app');
    const loading = document.getElementById('loading');

    async function init() {
        try {
            // TODO: Initialize mobile app
            //  - Auth check (reuse api-facade)
            //  - Render mobile UI
            //  - Setup touch gestures, etc.

            // Hide loading once ready
            loading.style.display = 'none';

            console.log('[SI3LN Mobile] Ready');
        } catch (err) {
            console.error('[SI3LN Mobile] Init failed:', err);
            loading.innerHTML = '<p>Erreur de chargement. Réessayez.</p>';
        }
    }

    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
