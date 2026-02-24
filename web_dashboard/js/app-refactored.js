// app.js - Main application controller (refactored)
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
        
        // Initialize modules
        this.profileManager = new ProfileManager(window.api);
        this.gamesManager = new GamesManager();
        this.authManager = new AuthManager(window.api);
        this.helpManager = new HelpManager();
        this.mobileManager = new MobileManager();
        
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
        
        // Check auth and load initial data
        this.checkAuth();
        this.loadHomeData();
    }
    
    initMenuHandlers() {
        // Toggle menu avec le triangle PLAY
        this.menuTrigger?.addEventListener('click', () => {
            this.menuDropdown.classList.toggle('visible');
        });
        
        // Fermer le menu si on clique ailleurs
        document.addEventListener('click', (e) => {
            if (!this.menuTrigger.contains(e.target) && !this.menuDropdown.contains(e.target)) {
                this.menuDropdown.classList.remove('visible');
            }
        });
        
        // Navigation dans le menu
        this.menuItems.forEach(item => {
            item.addEventListener('click', () => {
                const page = item.dataset.page;
                if (page) {
                    this.navigateTo(page);
                    this.menuDropdown.classList.remove('visible');
                }
            });
        });
    }
    
    initAuthHandlers() {
        // Logout
        this.logoutBtn?.addEventListener('click', () => this.logout());
        
        // Top bar login link
        const topLoginLink = document.getElementById('topLoginLink');
        if (topLoginLink) {
            topLoginLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.navigateTo('login');
            });
        }
    }
    
    initNavigationHandlers() {
        // Lien vers le jeu
        this.playGameLink?.addEventListener('click', (e) => {
            e.preventDefault();
            this.navigateTo('games');
        });
        
        // "Already have an account? Login" link on create-account page → go to login
        const loginRedirect = document.getElementById('loginRedirect');
        if (loginRedirect) {
            loginRedirect.addEventListener('click', (e) => {
                e.preventDefault();
                this.navigateTo('login');
            });
        }
        
        // "Create account" link on login page → go to create-account (also handled in auth.js)
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
        // Page logo handlers (ARCAD3X headers on pages)
        const pageLogos = document.querySelectorAll('.page-logo');
        pageLogos.forEach(logo => {
            logo.addEventListener('click', (e) => {
                e.preventDefault();
                const targetPage = logo.getAttribute('data-page') || 'home';
                this.navigateTo(targetPage);
            });
        });
        
        // Sidebar menu logo (main ARCAD3X logo)
        const menuLogo = document.querySelector('.menu-logo');
        if (menuLogo) {
            menuLogo.style.cursor = 'pointer';
            menuLogo.addEventListener('click', () => {
                this.navigateTo('home');
                this.menuDropdown.classList.remove('visible');
            });
        }

        // Top-bar site title link (ARCAD3X in top bar)
        const topBarTitle = document.querySelector('.top-bar-title a[data-page]');
        if (topBarTitle) {
            topBarTitle.addEventListener('click', (e) => {
                e.preventDefault();
                const targetPage = topBarTitle.getAttribute('data-page') || 'home';
                this.navigateTo(targetPage);
            });
        }
    }

    initLanguageSwitcher() {
        const languageBtn = document.getElementById('languageBtn');
        const languageDropdown = document.getElementById('languageDropdown');
        const languageOptions = document.querySelectorAll('.language-option');
        const currentLanguageDisplay = document.getElementById('currentLanguage');
        
        // Update current language display
        const updateLanguageDisplay = () => {
            const currentLang = window.i18n.getLanguage().toUpperCase();
            if (currentLanguageDisplay) {
                currentLanguageDisplay.textContent = currentLang;
            }
            
            // Update active state
            languageOptions.forEach(option => {
                const lang = option.getAttribute('data-lang');
                if (lang === window.i18n.getLanguage()) {
                    option.classList.add('active');
                } else {
                    option.classList.remove('active');
                }
            });
        };
        
        // Toggle dropdown
        if (languageBtn) {
            languageBtn.addEventListener('click', (e) => {
                e.stopPropagation();
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
                    
                    // Add animation
                    languageBtn?.classList.add('changing');
                    setTimeout(() => {
                        languageBtn?.classList.remove('changing');
                    }, 300);
                }
            });
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!languageBtn?.contains(e.target) && !languageDropdown?.contains(e.target)) {
                languageDropdown?.classList.remove('visible');
            }
        });
        
        // Initial display
        updateLanguageDisplay();
    }

    navigateTo(pageName) {
        // Cacher toutes les pages
        this.pages.forEach(page => page.classList.add('hidden'));
        
        // Afficher la bonne page
        const targetPage = document.getElementById(`${pageName}-page`);
        if (targetPage) {
            targetPage.classList.remove('hidden');
            this.loadPageData(pageName);
        } else {
            // Par défaut, retour à l'accueil
            document.getElementById('home-page')?.classList.remove('hidden');
        }
        
        // Pages spéciales - gestion du mode plein écran
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
        try {
            // Load leaderboard — API returns a flat array of {player_username, score, ...}
            const leaderboardData = await window.api.getLeaderboard(3);
            const leaderboardDiv = document.getElementById('leaderboard');
            if (Array.isArray(leaderboardData) && leaderboardDiv) {
                leaderboardDiv.innerHTML = leaderboardData
                    .map((entry, i) => `<div class="lb-entry">
                        <span class="lb-rank">#${i + 1}</span>
                        <span class="lb-name">${entry.player_username}</span>
                        <span class="lb-score">${entry.score} pts</span>
                    </div>`)
                    .join('');
            }
            
            // Show welcome message if logged in
            const token = localStorage.getItem('access_token');
            if (token) {
                try {
                    const profileData = await window.api.getCurrentPlayer();
                    const profileDiv = document.getElementById('profile');
                    if (profileDiv && profileData) {
                        profileDiv.innerHTML = `Welcome, ${profileData.display_name || profileData.username}!`;
                    }
                } catch (_) { /* not logged in */ }
            }
            
        } catch (error) {
            console.error('Erreur chargement home:', error);
        }
    }

    loadHelp() {
        document.getElementById('helpContent').innerHTML = `
            <div class="help-section">
                <h2>Comment jouer ?</h2>
                <p>Documentation à venir...</p>
            </div>
        `;
    }
    
    loadAbout() {
        document.getElementById('aboutContent').innerHTML = `
            <div class="about-section">
                <h2>À propos de nous</h2>
                <p>Projet SI3LN par Hugex & Schps...</p>
                <p>FullStack gaming platform</p>
            </div>
        `;
    }
    
    async loadSettings() {
        // Only allow admin / staff
        const role = window.api?.getLocalRole() ?? 'guest';
        if (role !== 'admin') {
            this.navigateTo('home');
            return;
        }

        try {
            const stats = await window.api.getStats().catch(() => null);
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
            console.error('Error loading settings:', error);
        }
    }

    checkAuth() {
        const token = localStorage.getItem('access_token');
        const isLoggedIn = !!token;
        const username = isLoggedIn ? (window.api?.getLocalUsername?.() ?? '') : '';
        this.authManager.updateAuthUI(isLoggedIn, username);
    }

    logout() {
        localStorage.removeItem('access_token');
        this.authManager.updateAuthUI(false);
        this.navigateTo('home');
    }
}

// ── Bootstrap ─────────────────────────────────────────────────────────────────
// window.api is already set by api.js (loaded before this file).
// We only need to create AppManager here.
document.addEventListener('DOMContentLoaded', () => {
    // Ensure api client exists (safety – api.js loads first anyway)
    if (!window.api) { window.api = new APIClient(); }
    window.app = new AppManager();
});
