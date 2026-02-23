// games.js - Games management module
class GamesManager {
    constructor() {
        this.currentGameId = null;
        this.currentGameIndex = 0;
        this.gameSession = null;
        this.isFullscreen = false;
        this.games = [
            {
                id: 'si3ln',
                name: 'SI3LN',
                description: 'Space Invaders III Last Night',
                url: 'game/index.html',  // Placeholder - see GAME_INTEGRATION.md
                thumbnail: 'assets/worlds/home_page.png'
            },
            {
                id: 'game2',
                name: 'Space Warriors',
                description: 'Coming Soon',
                comingSoon: true
            },
            {
                id: 'game3',
                name: 'Fantasy Quest',
                description: 'Coming Soon',
                comingSoon: true
            }
        ];
    }

    loadGames() {
        // Games are loaded via HTML, this is for dynamic updates
        console.log('Games page loaded');
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
        
        // Show loading
        const loadingElement = document.getElementById('gameLoading');
        if (loadingElement) {
            loadingElement.style.display = 'flex';
        }
        
        try {
            // Check if user is logged in
            const token = localStorage.getItem('access_token');
            const isGuest = !token;
            
            if (isGuest) {
                // Guest mode - show info
                this.showGuestInfo();
            } else {
                // Registered user - create game session
                await this.startGameSession();
            }
            
            // Load game in iframe
            setTimeout(() => {
                if (loadingElement) {
                    loadingElement.style.display = 'none';
                }
                const gameFrame = document.getElementById('gameFrame');
                const gameNameDisplay = document.getElementById('currentGameName');
                if (gameFrame) {
                    // Build URL with world/level/player params so the Wasm module can read them
                    const world = 'Space';   // TODO: let user choose world on games page
                    const level = 1;
                    const playerIndex = this.currentGameIndex || 0;
                    const gameUrl = `${game.url || 'game/index.html'}?world=${world}&level=${level}&player=${playerIndex}`;
                    gameFrame.src = gameUrl;
                }
                if (gameNameDisplay) {
                    gameNameDisplay.textContent = game.name;
                }
            }, 1500);
            
        } catch (error) {
            console.error('Error launching game:', error);
            if (loadingElement) {
                loadingElement.style.display = 'none';
            }
            alert('Error launching game. Please try again.');
        }
    }
    
    showGuestInfo() {
        const guestInfo = document.getElementById('guestInfo');
        if (guestInfo) {
            guestInfo.style.display = 'block';
            setTimeout(() => {
                guestInfo.style.display = 'none';
            }, 5000);
        }
    }
    
    async startGameSession() {
        try {
            // Get actual player_id from JWT token
            const token = localStorage.getItem('access_token');
            if (!token) throw new Error('Not authenticated');
            const payload = JSON.parse(atob(token.split('.')[1]));
            const playerId = payload.player_id;

            const response = await window.api.createGameSession(playerId, 1);
            this.gameSession = response;
            console.log('Game session started:', this.gameSession);
        } catch (error) {
            console.error('Error starting game session:', error);
        }
    }
    
    async endGameSession(score, level) {
        if (!this.gameSession) return;
        
        try {
            await window.api.request(`/game/sessions/${this.gameSession.id}`, {
                method: 'PATCH',
                body: JSON.stringify({
                    score: score,
                    level_reached: level,
                    ended_at: new Date().toISOString()
                })
            });
            
            console.log('Game session ended');
            this.gameSession = null;
        } catch (error) {
            console.error('Error ending game session:', error);
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
        
        // Switch to next game
        this.launchGame(nextGame.id);
    }
    
    toggleFullscreen() {
        const gameContainer = document.getElementById('game-play-page');
        
        if (!document.fullscreenElement) {
            gameContainer.requestFullscreen().then(() => {
                this.isFullscreen = true;
                this.updateFullscreenUI();
            }).catch(err => {
                console.error('Error attempting to enable fullscreen:', err);
            });
        } else {
            document.exitFullscreen().then(() => {
                this.isFullscreen = false;
                this.updateFullscreenUI();
            });
        }
    }
    
    updateFullscreenUI() {
        const fullscreenBtn = document.getElementById('fullscreenBtn');
        if (fullscreenBtn) {
            fullscreenBtn.textContent = this.isFullscreen ? '⊡ Exit Fullscreen' : '⛶ Fullscreen';
        }
    }

    toggleGameMenu() {
        // Ouvrir le menu latéral depuis le jeu
        const sideMenu = document.getElementById('sideMenu');
        if (sideMenu) {
            sideMenu.classList.toggle('visible');
        }
    }

    initGameControls() {
        // Game card click handlers
        const si3lnCard = document.getElementById('si3lnGameCard');
        if (si3lnCard) {
            si3lnCard.addEventListener('click', () => {
                this.launchGame('si3ln');
            });
        }
        
        // Navigation buttons
        const prevBtn = document.getElementById('prevGameBtn');
        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                this.navigateGame('prev');
            });
        }
        
        const nextBtn = document.getElementById('nextGameBtn');
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                this.navigateGame('next');
            });
        }
        
        // Fullscreen button
        const fullscreenBtn = document.getElementById('fullscreenBtn');
        if (fullscreenBtn) {
            fullscreenBtn.addEventListener('click', () => {
                this.toggleFullscreen();
            });
        }
        
        // Exit game button
        const exitGameBtn = document.getElementById('exitGameBtn');
        if (exitGameBtn) {
            exitGameBtn.addEventListener('click', () => {
                if (confirm('Exit game? Your progress will be saved.')) {
                    if (this.gameSession) {
                        // Get score from game iframe if possible
                        this.endGameSession(0, 1);
                    }
                    window.app.navigateTo('games');
                }
            });
        }
        
        // Listen for fullscreen changes
        document.addEventListener('fullscreenchange', () => {
            this.isFullscreen = !!document.fullscreenElement;
            this.updateFullscreenUI();
        });
    }
}

// Export for use in main app
window.GamesManager = GamesManager;
