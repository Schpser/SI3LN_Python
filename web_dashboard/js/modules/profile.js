// profile.js - Profile management module
class ProfileManager {
    constructor(apiClient) {
        this.api = apiClient;
        this._editBtnInitialized = false;
    }

    async loadProfile() {
        try {
            const token = localStorage.getItem('access_token');
            
            if (!token) {
                this.showPublicProfile('guest');
                return;
            }
            
            // Load profile data
            const profileData = await this.api.getCurrentPlayer();
            this.updateProfileDisplay(profileData);
            this.toggleEditButton(true);
            
            // Load best scores from sessions
            const payload = JSON.parse(atob(token.split('.')[1]));
            await this.loadBestScores(payload.player_id);
            
        } catch (error) {
            console.error('Erreur chargement profil:', error);
        }
    }

    async loadBestScores(playerId) {
        try {
            const sessions = await this.api.getGameSessions(playerId);
            const scoresList = document.getElementById('bestScoresList');
            if (!scoresList) return;

            if (!sessions || sessions.length === 0) {
                scoresList.innerHTML = '<div class="score-item">No games played yet!</div>';
                return;
            }

            // Sort by score descending, take top 5
            const top5 = sessions
                .sort((a, b) => b.score - a.score)
                .slice(0, 5);

            scoresList.innerHTML = top5.map((s, i) =>
                `<div class="score-item">
                    <span class="score-rank">#${i + 1}</span>
                    <span class="score-value">${s.score} pts</span>
                    <span class="score-level">Level ${s.level_reached}</span>
                </div>`
            ).join('');
        } catch (error) {
            const scoresList = document.getElementById('bestScoresList');
            if (scoresList) scoresList.innerHTML = '<div class="score-item">Login to see scores</div>';
        }
    }


    updateProfileDisplay(profile) {
        // Infos de base — use username (display_name not in schema)
        const displayName = profile.username || 'Player';
        document.getElementById('profileDisplayName').textContent = displayName;
        document.getElementById('profileUsername').textContent = profile.username || '';

        // Avatar (not stored in backend yet - use default)
        document.getElementById('profileAvatarLarge').src = 'assets/players/1000055338.png';

        // Bio (not stored in backend yet)
        const bioElement = document.getElementById('userBio');
        bioElement.innerHTML = '<p class="bio-placeholder">No description yet...</p>';

        // Stats globales (proviennent de EnhancedProfileSchema)
        const statsEl = document.getElementById('profileStats');
        if (statsEl) {
            statsEl.innerHTML = `
                <div class="stat-card"><span class="stat-value">${profile.total_score ?? 0}</span><span class="stat-label">Total Score</span></div>
                <div class="stat-card"><span class="stat-value">${profile.games_played ?? 0}</span><span class="stat-label">Games Played</span></div>
                <div class="stat-card"><span class="stat-value">${profile.highest_level ?? 1}</span><span class="stat-label">Highest Level</span></div>
                <div class="stat-card"><span class="stat-value">${profile.achievements_count ?? 0}</span><span class="stat-label">Achievements</span></div>
            `;
        }

        // Scores are loaded separately by loadBestScores()

        // Jeux favoris (disabled until game is ready)
        const favoritesGrid = document.getElementById('favoritesGrid');
        if (favoritesGrid) {
            favoritesGrid.innerHTML = '<div class="favorite-item">⭐ Favorites coming soon!</div>';
        }
    }

    toggleEditButton(show) {
        const editBtn = document.getElementById('editProfileBtn');
        if (!editBtn) return;
        if (show) {
            editBtn.classList.remove('hidden');
            // Use onclick to avoid accumulating duplicate listeners
            editBtn.onclick = () => this.openEditModal();
        } else {
            editBtn.classList.add('hidden');
            editBtn.onclick = null;
        }
    }

    openEditModal() {
        const modal = document.getElementById('editProfileModal');
        modal.classList.remove('hidden');
        
        // Pré-remplir avec les données actuelles
        this.populateEditModal();
        
        // Gérer la fermeture
        modal.querySelector('.modal-close').addEventListener('click', () => {
            modal.classList.add('hidden');
        });
        
        modal.querySelector('.cancel-btn').addEventListener('click', () => {
            modal.classList.add('hidden');
        });
        
        // Gérer la sauvegarde
        document.getElementById('saveProfileBtn').addEventListener('click', () => {
            this.saveProfileChanges();
        });
        
        // Gérer le compteur de caractères
        const bioTextarea = document.getElementById('editBio');
        bioTextarea.addEventListener('input', () => {
            document.getElementById('bioCharCount').textContent = bioTextarea.value.length;
        });
        
        // Gérer la sélection des couleurs
        document.querySelectorAll('.color-option').forEach(option => {
            option.addEventListener('click', () => {
                document.querySelectorAll('.color-option').forEach(opt => opt.classList.remove('selected'));
                option.classList.add('selected');
            });
        });
        
        // Gérer l'upload d'avatar
        document.getElementById('avatarUpload').addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                if (file.size > 5 * 1024 * 1024) {
                    alert('File too big! Max 5MB');
                    return;
                }
                // Preview
                const reader = new FileReader();
                reader.onload = (e) => {
                    document.getElementById('profileAvatarLarge').src = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        });
    }

    populateEditModal() {
        // Remplir avec les données actuelles
        const currentBio = document.querySelector('#userBio p')?.textContent || '';
        document.getElementById('editBio').value = currentBio;
        document.getElementById('bioCharCount').textContent = currentBio.length;
        
        // Cocher la bonne couleur
        const currentBg = document.querySelector('.profile-container').style.backgroundColor;
        if (currentBg) {
            document.querySelectorAll('.color-option').forEach(opt => {
                if (opt.dataset.color === currentBg) {
                    opt.classList.add('selected');
                }
            });
        }
    }

    async saveProfileChanges() {
        const modal = document.getElementById('editProfileModal');
        
        // Récupérer les données – only send fields the backend accepts (ProfileUpdateSchema)
        const username = document.getElementById('profileUsername')?.textContent;
        const email = null; // email editing not yet exposed in the modal
        
        const updates = {};
        if (username) updates.username = username;
        if (email) updates.email = email;
        
        try {
            // Use PATCH /game/profile/me which accepts ProfileUpdateSchema
            await this.api.request('/game/profile/me', {
                method: 'PATCH',
                body: JSON.stringify(updates)
            });
            modal.classList.add('hidden');
            this.loadProfile(); // Recharger le profil
        } catch (error) {
            console.error('Erreur sauvegarde:', error);
            alert('Error saving changes');
        }
    }

    showPublicProfile(username) {
        // Afficher une version publique du profil
        document.getElementById('profileDisplayName').textContent = username || 'Guest';
        document.getElementById('profileUsername').textContent = username || 'guest';
        document.getElementById('userBio').innerHTML = '<p class="bio-placeholder">User not logged in</p>';
        document.getElementById('bestScoresList').innerHTML = '<div class="score-item">Login to see scores</div>';
        document.getElementById('favoritesGrid').innerHTML = '<div class="favorite-item">Login to see favorites</div>';
        document.getElementById('editProfileBtn').classList.add('hidden');
    }
}

// Export for use in main app
window.ProfileManager = ProfileManager;
