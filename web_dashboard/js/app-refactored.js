// app.js - Main application controller (v2 — refactored with facade + search)
// =============================================================================

'use strict';

class AppManager {
    constructor() {
        // DOM elements
        this.menuTrigger = document.getElementById('menuTrigger');
        this.menuDropdown = document.getElementById('menuDropdown');
        this.menuItems = document.querySelectorAll('.menu-item');
        this.pages = document.querySelectorAll('.page');
        this.logoutBtn = document.getElementById('logoutBtn');
        this.userInfo = document.getElementById('userInfo');
        this.userName = document.getElementById('userName');
        this.playGameLink = document.getElementById('playGameLink');
        
        // Create the secure facade service (wraps the raw API client)
        if (typeof ApiFacadeService !== 'undefined' && window._rawApiClient) {
            window.facade = new ApiFacadeService(window._rawApiClient);
        }
        
        // Initialize modules
        this.profileManager = new ProfileManager(window.api);
        this.gamesManager = new GamesManager();
        this.authManager = new AuthManager(window.api);
        this.helpManager = new HelpManager();
        this.mobileManager = new MobileManager();
        
        // Search service
        if (typeof SearchService !== 'undefined') {
            this.searchService = new SearchService(window.facade || window.api);
        }
        
        this.init();
    }
    
    init() {
        // Initialize i18n first
        window.i18n.init();
        
        this.initMenuHandlers();
        this.initAuthHandlers();
        this.initNavigationHandlers();
        this.initLogoHandlers();
        this.initLanguageSwitcher();
        this.initSearch();
        
        // Initialize mobile and touch support
        this.mobileManager.init();
        
        // Initialize game controls
        this.gamesManager.initGameControls();
        
        // Initialize help page
        this.helpManager.initHelpHandlers();
        
        // Initialize login page
        this.authManager.initLoginPage();
        
        // Initialize signup validation
        this.authManager.initSignupValidation();
        
        // Display version in console (safe)
        if (window.APP_CONFIG) {
            if (window.AppLogger) window.AppLogger.log(
                `${window.APP_CONFIG.APP_NAME} v${window.APP_CONFIG.VERSION}`
            );
        }
        
        // Check auth and load initial data
        this.checkAuth();
        this.loadHomeData();
    }
    
    initMenuHandlers() {
        this.menuTrigger?.addEventListener('click', () => {
            this.menuDropdown.classList.toggle('visible');
        });
        
        document.addEventListener('click', (e) => {
            if (!this.menuTrigger?.contains(e.target) && !this.menuDropdown?.contains(e.target)) {
                this.menuDropdown?.classList.remove('visible');
            }
        });
        
        this.menuItems.forEach(item => {
            item.addEventListener('click', () => {
                const page = item.dataset.page;
                if (page) {
                    this.navigateTo(page);
                    this.menuDropdown?.classList.remove('visible');
                }
            });
        });
    }
    
    initAuthHandlers() {
        this.logoutBtn?.addEventListener('click', () => this.logout());
        
        const topLoginLink = document.getElementById('topLoginLink');
        if (topLoginLink) {
            topLoginLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.navigateTo('login');
            });
        }
    }
    
    initNavigationHandlers() {
        // "Already have an account? Login" link
        const loginRedirect = document.getElementById('loginRedirect');
        if (loginRedirect) {
            loginRedirect.addEventListener('click', (e) => {
                e.preventDefault();
                this.navigateTo('login');
            });
        }
        
        // "Create account" link on login page
        const signupLink = document.getElementById('signupLink');
        if (signupLink && !signupLink._navHandled) {
            signupLink._navHandled = true;
            signupLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.navigateTo('create-account');
            });
        }
    }
    
    initLogoHandlers() {
        document.querySelectorAll('.page-logo').forEach(logo => {
            logo.addEventListener('click', (e) => {
                e.preventDefault();
                this.navigateTo(logo.getAttribute('data-page') || 'home');
            });
        });
        
        const menuLogo = document.querySelector('.menu-logo');
        if (menuLogo) {
            menuLogo.style.cursor = 'pointer';
            menuLogo.addEventListener('click', () => {
                this.navigateTo('home');
                this.menuDropdown?.classList.remove('visible');
            });
        }

        const topBarTitle = document.querySelector('.top-bar-title a[data-page]');
        if (topBarTitle) {
            topBarTitle.addEventListener('click', (e) => {
                e.preventDefault();
                this.navigateTo(topBarTitle.getAttribute('data-page') || 'home');
            });
        }
    }

    initLanguageSwitcher() {
        const languageBtn = document.getElementById('languageBtn');
        const languageDropdown = document.getElementById('languageDropdown');
        const languageOptions = document.querySelectorAll('.language-option');
        const currentLanguageDisplay = document.getElementById('currentLanguage');
        
        const updateLanguageDisplay = () => {
            const currentLang = window.i18n.getLanguage().toUpperCase();
            if (currentLanguageDisplay) {
                currentLanguageDisplay.textContent = currentLang;
            }
            languageOptions.forEach(option => {
                const lang = option.getAttribute('data-lang');
                option.classList.toggle('active', lang === window.i18n.getLanguage());
            });
        };
        
        // Toggle dropdown — remove .hidden (if present from HTML), toggle .visible
        if (languageBtn) {
            languageBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                // Ensure .hidden doesn't block the dropdown
                languageDropdown?.classList.remove('hidden');
                languageDropdown?.classList.toggle('visible');
            });
        }
        
        // Change language
        languageOptions.forEach(option => {
            option.addEventListener('click', () => {
                const lang = option.getAttribute('data-lang');
                if (lang) {
                    window.i18n.setLanguage(lang);
                    updateLanguageDisplay();
                    languageDropdown?.classList.remove('visible');
                    
                    languageBtn?.classList.add('changing');
                    setTimeout(() => languageBtn?.classList.remove('changing'), 300);
                }
            });
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!languageBtn?.contains(e.target) && !languageDropdown?.contains(e.target)) {
                languageDropdown?.classList.remove('visible');
            }
        });
        
        updateLanguageDisplay();
    }

    // ── Search ────────────────────────────────────────────────────────────────

    initSearch() {
        const searchInput = document.querySelector('.search-input');
        const searchButton = document.querySelector('.search-button');
        
        if (!searchInput) return;
        
        // Create search results dropdown
        const searchContainer = searchInput.closest('.search-container');
        let resultsDropdown = document.getElementById('searchResults');
        if (!resultsDropdown && searchContainer) {
            resultsDropdown = document.createElement('div');
            resultsDropdown.id = 'searchResults';
            resultsDropdown.className = 'search-results-dropdown';
            searchContainer.appendChild(resultsDropdown);
        }
        
        // Live search on input
        searchInput.addEventListener('input', () => {
            const query = searchInput.value.trim();
            if (query.length < 2) {
                this._hideSearchResults();
                return;
            }
            
            if (this.searchService) {
                this.searchService.debounceSearch(query, (results) => {
                    this._renderSearchResults(results, resultsDropdown);
                });
            }
        });
        
        // Search button click
        searchButton?.addEventListener('click', () => {
            const query = searchInput.value.trim();
            if (query.length >= 2 && this.searchService) {
                this.searchService.search(query).then(results => {
                    this._renderSearchResults(results, resultsDropdown);
                });
            }
        });
        
        // Enter key
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                searchButton?.click();
            }
            if (e.key === 'Escape') {
                this._hideSearchResults();
                searchInput.blur();
            }
        });
        
        // Close results when clicking outside
        document.addEventListener('click', (e) => {
            if (!searchContainer?.contains(e.target)) {
                this._hideSearchResults();
            }
        });
    }

    _renderSearchResults(results, dropdown) {
        if (!dropdown) return;
        
        if (!results || results.length === 0) {
            dropdown.innerHTML = '<div class="search-no-results">No results found</div>';
            dropdown.classList.add('visible');
            return;
        }
        
        dropdown.innerHTML = results.map(result => `
            <div class="search-result-item" data-type="${result.type}" data-id="${result.id}" 
                 data-action="${result.action || ''}" data-section="${result.section || ''}">
                <span class="search-result-icon">${result.icon}</span>
                <div class="search-result-info">
                    <span class="search-result-title">${this._escapeHtml(result.title)}</span>
                    <span class="search-result-type">${result.description || result.type}</span>
                </div>
            </div>
        `).join('');
        
        dropdown.classList.add('visible');
        
        // Handle clicks on results
        dropdown.querySelectorAll('.search-result-item').forEach(item => {
            item.addEventListener('click', () => {
                this._handleSearchResultClick(item);
                this._hideSearchResults();
                document.querySelector('.search-input').value = '';
            });
        });
    }

    _handleSearchResultClick(item) {
        const type = item.dataset.type;
        const id = item.dataset.id;
        const action = item.dataset.action;
        const section = item.dataset.section;
        
        switch(action) {
            case 'launch-game':
                this.gamesManager.launchGame(id);
                break;
            case 'show-help':
                this.navigateTo('help');
                setTimeout(() => this.helpManager.showHelpDetail(section), 100);
                break;
            case 'show-profile':
                this.navigateTo('profile');
                break;
            default:
                if (type === 'game') this.navigateTo('games');
                else if (type === 'help') this.navigateTo('help');
                else if (type === 'player') this.navigateTo('profile');
                break;
        }
    }

    _hideSearchResults() {
        const dropdown = document.getElementById('searchResults');
        if (dropdown) {
            dropdown.classList.remove('visible');
            dropdown.innerHTML = '';
        }
    }

    _escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ── Navigation ────────────────────────────────────────────────────────────

    navigateTo(pageName) {
        this.pages.forEach(page => page.classList.add('hidden'));
        
        const targetPage = document.getElementById(`${pageName}-page`);
        if (targetPage) {
            targetPage.classList.remove('hidden');
            this.loadPageData(pageName);
        } else {
            document.getElementById('home-page')?.classList.remove('hidden');
        }
        
        if (pageName === 'game-play') {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = '';
        }
    }
    
    async loadPageData(pageName) {
        switch(pageName) {
            case 'profile':
                await this.profileManager.loadProfile();
                break;
            case 'games':
                this.gamesManager.loadGames();
                break;
            case 'help':
                this.helpManager.showHelpMenu();
                break;
            case 'settings':
                await this.loadSettings();
                break;
            case 'about':
                this.loadAbout();
                break;
        }
    }
    
    async loadHomeData() {
        // Load leaderboard
        try {
            const facade = window.facade;
            const leaderboardData = facade
                ? await facade.getLeaderboard(3)
                : await window.api.getLeaderboard(3);
            
            const leaderboardDiv = document.getElementById('leaderboard');
            if (Array.isArray(leaderboardData) && leaderboardDiv) {
                if (leaderboardData.length === 0) {
                    leaderboardDiv.innerHTML = '<p>No scores yet. Be the first to play!</p>';
                } else {
                    leaderboardDiv.innerHTML = leaderboardData
                        .map((entry, i) => `<div class="lb-entry">
                            <span class="lb-rank">#${i + 1}</span>
                            <span class="lb-name">${entry.player_username || 'Unknown'}</span>
                            <span class="lb-score">${entry.score} pts</span>
                        </div>`)
                        .join('');
                }
            }
        } catch (error) {
            const leaderboardDiv = document.getElementById('leaderboard');
            if (leaderboardDiv) leaderboardDiv.innerHTML = '<p>Could not load leaderboard.</p>';
        }

        // Show welcome message if logged in
        const facade = window.facade;
        const tokenKey = window.APP_CONFIG?.TOKEN_KEY || 'access_token';
        const isAuth = facade ? facade.isAuthenticated() : !!localStorage.getItem(tokenKey);
        if (isAuth) {
            try {
                const profileData = facade
                    ? await facade.getCurrentPlayer()
                    : await window.api.getCurrentPlayer();
                const profileDiv = document.getElementById('profile');
                if (profileDiv && profileData) {
                    profileDiv.innerHTML = `Welcome, ${profileData.username || 'Player'}!`;
                }
            } catch (error) {
                const profileDiv = document.getElementById('profile');
                if (profileDiv) {
                    const username = facade?.getLocalUsername() || window.api?.getLocalUsername();
                    profileDiv.innerHTML = username ? `Welcome, ${username}!` : 'Please log in';
                }
            }
        }
    }

    loadAbout() {
        const el = document.getElementById('aboutContent');
        if (el) {
            const version = window.APP_CONFIG?.VERSION || '1.0.0';
            el.innerHTML = `
                <div class="about-section">
                    <h2>À propos de nous</h2>
                    <p>Projet SI3LN par Hugex & Schps...</p>
                    <p>FullStack gaming platform</p>
                    <p class="version-info">Version ${version}</p>
                </div>
            `;
        }
    }
    
    async loadSettings() {
        const role = window.facade?.getLocalRole() || window.api?.getLocalRole() || 'guest';
        if (role !== 'admin') {
            this.navigateTo('home');
            return;
        }

        try {
            const stats = await (window.facade || window.api).getStats().catch(() => null);
            const statsHtml = stats
                ? `<ul>
                    <li>Players: <b>${stats.total_players}</b></li>
                    <li>Sessions: <b>${stats.total_sessions}</b></li>
                    <li>Highest Score: <b>${stats.highest_score}</b></li>
                    <li>Avg Score: <b>${stats.average_score}</b></li>
                   </ul>`
                : '<p>Could not load stats.</p>';

            document.getElementById('settingsContent').innerHTML = `
                <div class="admin-panel">
                    <h2>Settings</h2>
                    <p><a href="/admin/" target="_blank">Open Django Admin Panel</a></p>
                    <h3>Platform Statistics</h3>
                    ${statsHtml}
                </div>
            `;
        } catch (error) {
            if (window.AppLogger) window.AppLogger.error('Settings load error');
        }
    }

    checkAuth() {
        const facade = window.facade;
        const tokenKey = window.APP_CONFIG?.TOKEN_KEY || 'access_token';
        const isLoggedIn = facade ? facade.isAuthenticated() : !!localStorage.getItem(tokenKey);
        const username = isLoggedIn
            ? (facade?.getLocalUsername() || window.api?.getLocalUsername() || '')
            : '';
        this.authManager.updateAuthUI(isLoggedIn, username);
    }

    logout() {
        if (window.facade) {
            window.facade.logout();
        } else {
            localStorage.removeItem(window.APP_CONFIG?.TOKEN_KEY || 'access_token');
            localStorage.removeItem(window.APP_CONFIG?.LEGACY_TOKEN_KEY || 'SI3LN_SESSION');
        }
        this.authManager.updateAuthUI(false);
        this.navigateTo('home');
    }
}

// ── Bootstrap ─────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    if (!window.api) { window.api = new APIClient(); }
    window.app = new AppManager();
});
