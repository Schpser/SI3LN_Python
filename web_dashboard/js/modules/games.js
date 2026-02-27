// games.js - Games management module (v2 — fixed launch + responsive + bg color)
// ================================================================================

'use strict';

class GamesManager {
    constructor() {
        this.currentGameId = null;
        this.currentGameIndex = 0;
        this.gameSession = null;
        this.isFullscreen = false;
        // Use GameEntity catalog if available, else inline fallback
        this.games = (typeof GameEntity !== 'undefined')
            ? GameEntity.catalog()
            : [
                { id: 'si3ln', name: 'SI3LN', description: 'Space Invaders III Last Night',
                  url: 'game/index.html', thumbnail: 'assets/worlds/home_page.jpg',
                  homepageBg: '#000428', homepageImage: 'assets/worlds/home_page.jpg',
                  isPlayable: true, comingSoon: false },
                { id: 'game2', name: 'Space Warriors', description: 'Coming Soon',
                  comingSoon: true, isPlayable: false },
                { id: 'game3', name: 'Fantasy Quest', description: 'Coming Soon',
                  comingSoon: true, isPlayable: false },
              ];
    }

    loadGames() {
        // Games are rendered via HTML; this hook is for future dynamic loading
    }

    async launchGame(gameId) {
        this.currentGameId = gameId;
        const game = this.games.find(g => g.id === gameId);
        
        if (!game || game.comingSoon) {
            alert('This game is coming soon!');
            return;
        }
        
        // Navigate to game play page
        if (window.app) {
            window.app.navigateTo('game-play');
        }
        
        // Apply game-specific background color behind the iframe
        this._applyGameBackground(game);
        
        // Show loading
        const loadingElement = document.getElementById('gameLoading');
        if (loadingElement) loadingElement.style.display = 'flex';
        
        // Check auth — use facade if available, else fall back to localStorage
        const facade = window.facade;
        const tokenKey = window.APP_CONFIG?.TOKEN_KEY || 'access_token';
        const isAuthenticated = facade
            ? facade.isAuthenticated()
            : !!localStorage.getItem(tokenKey);
        
        if (!isAuthenticated) {
            this.showGuestInfo();
        } else {
            // Logged-in: create game session (non-blocking)
            this._startGameSession().catch(err => {
                if (window.AppLogger) window.AppLogger.warn('Session creation failed (non-blocking)');
            });
        }

        // Load the game iframe after a short delay for the loading animation
        setTimeout(() => {
            if (loadingElement) loadingElement.style.display = 'none';
            
            const gameFrame = document.getElementById('gameFrame');
            const gameNameDisplay = document.getElementById('currentGameName');
            
            if (gameFrame) {
                const gameUrl = (game.url || 'game/index.html');
                gameFrame.src = gameUrl;
            }
            if (gameNameDisplay) {
                gameNameDisplay.textContent = game.name;
            }
        }, 1200);
    }

    /**
     * Apply the game's background color/image behind the iframe
     * so the area around the game matches the game's theme.
     */
    _applyGameBackground(game) {
        const container = document.querySelector('.game-fullscreen-container');
        const page = document.getElementById('game-play-page');
        
        if (page) {
            const bg = game.homepageBg || '#000428';
            page.style.backgroundColor = bg;
        }
        if (container) {
            const bg = game.homepageBg || '#000428';
            container.style.backgroundColor = bg;
            
            // If there's a homepage image, use it as a blurred background
            if (game.homepageImage || game.thumbnail) {
                const imgUrl = game.homepageImage || game.thumbnail;
                container.style.backgroundImage = `url('${imgUrl}')`;
                container.style.backgroundSize = 'cover';
                container.style.backgroundPosition = 'center';
            }
        }
    }
    
    showGuestInfo() {
        const guestInfo = document.getElementById('guestInfo');
        if (guestInfo) {
            guestInfo.style.display = 'block';
            setTimeout(() => { guestInfo.style.display = 'none'; }, 8000);
        }
    }
    
    async _startGameSession() {
        try {
            const facade = window.facade;
            if (facade && facade.isAuthenticated()) {
                const session = await facade.createGameSession(null);
                this.gameSession = session;
            } else {
                // Fallback: direct API call
                const playerId = window.api?.getLocalPlayerId();
                if (!playerId) return;
                const session = await window.api.createGameSession(playerId, null);
                this.gameSession = session;
            }
        } catch (error) {
            if (window.AppLogger) window.AppLogger.error('Game session error');
        }
    }
    
    async endGameSession(score, level) {
        if (!this.gameSession) return;
        
        try {
            const facade = window.facade;
            if (facade) {
                await facade.endGameSession(this.gameSession.id, score, level);
            } else {
                await window.api.endGameSession(this.gameSession.id, score, level);
            }
            this.gameSession = null;
        } catch (error) {
            if (window.AppLogger) window.AppLogger.error('End session error');
        }
    }

    navigateGame(direction) {
        if (direction === 'prev') {
            this.currentGameIndex = (this.currentGameIndex - 1 + this.games.length) % this.games.length;
        } else {
            this.currentGameIndex = (this.currentGameIndex + 1) % this.games.length;
        }
        
        const nextGame = this.games[this.currentGameIndex];
        if (nextGame.comingSoon) {
            alert(`${nextGame.name} - Coming Soon!`);
            return;
        }
        this.launchGame(nextGame.id);
    }
    
    toggleFullscreen() {
        const gameContainer = document.getElementById('game-play-page') || document.documentElement;

        if (!document.fullscreenElement &&
            !document.webkitFullscreenElement &&
            !document.mozFullScreenElement &&
            !document.msFullscreenElement) {
            const requestFS = gameContainer.requestFullscreen
                || gameContainer.webkitRequestFullscreen
                || gameContainer.mozRequestFullScreen
                || gameContainer.msRequestFullscreen;

            if (requestFS) {
                requestFS.call(gameContainer).then(() => {
                    this.isFullscreen = true;
                    this.updateFullscreenUI();
                }).catch(() => {});
            }
        } else {
            const exitFS = document.exitFullscreen
                || document.webkitExitFullscreen
                || document.mozCancelFullScreen
                || document.msExitFullscreen;

            if (exitFS) {
                exitFS.call(document).then(() => {
                    this.isFullscreen = false;
                    this.updateFullscreenUI();
                }).catch(() => {});
            }
        }
    }

    updateFullscreenUI() {
        const fullscreenBtn = document.getElementById('fullscreenBtn');
        if (fullscreenBtn) {
            const icon = fullscreenBtn.querySelector('.control-icon');
            const text = fullscreenBtn.querySelector('.control-text');
            if (icon) icon.textContent = this.isFullscreen ? '⊡' : '⛶';
            if (text) text.textContent = this.isFullscreen ? 'Exit Fullscreen' : 'Fullscreen';
        }
    }

    toggleGameMenu() {
        const sideMenu = document.getElementById('sideMenu');
        if (sideMenu) sideMenu.classList.toggle('visible');
    }

    initGameControls() {
        // Game card click → launch
        const si3lnCard = document.getElementById('si3lnGameCard');
        si3lnCard?.addEventListener('click', () => this.launchGame('si3ln'));
        
        // Home page "Play now" link → launch
        const playLink = document.getElementById('playGameLink');
        if (playLink) {
            playLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.launchGame('si3ln');
            });
        }
        
        // Navigation buttons — only show if multiple games are playable
        const navContainer = document.querySelector('.game-navigation');
        const playableGames = this.games.filter(g => !g.comingSoon && g.isPlayable !== false);
        if (navContainer && playableGames.length > 1) {
            navContainer.classList.add('multi-game');
        }
        document.getElementById('prevGameBtn')?.addEventListener('click', () => this.navigateGame('prev'));
        document.getElementById('nextGameBtn')?.addEventListener('click', () => this.navigateGame('next'));
        
        // Fullscreen
        document.getElementById('fullscreenBtn')?.addEventListener('click', () => this.toggleFullscreen());
        
        // Exit game
        document.getElementById('exitGameBtn')?.addEventListener('click', () => {
            if (this.gameSession) {
                this.endGameSession(0, 1);
            }
            // Reset iframe
            const gameFrame = document.getElementById('gameFrame');
            if (gameFrame) gameFrame.src = 'about:blank';
            // Reset background
            const page = document.getElementById('game-play-page');
            if (page) page.style.backgroundColor = '';
            const container = document.querySelector('.game-fullscreen-container');
            if (container) {
                container.style.backgroundColor = '';
                container.style.backgroundImage = '';
            }
            
            if (window.app) window.app.navigateTo('games');
        });
        
        // Fullscreen change listener (cross-browser)
        const fsEvents = ['fullscreenchange', 'webkitfullscreenchange', 'mozfullscreenchange', 'MSFullscreenChange'];
        fsEvents.forEach(evt => {
            document.addEventListener(evt, () => {
                this.isFullscreen = !!(
                    document.fullscreenElement ||
                    document.webkitFullscreenElement ||
                    document.mozFullScreenElement ||
                    document.msFullscreenElement
                );
                this.updateFullscreenUI();
            });
        });
    }
}

window.GamesManager = GamesManager;
