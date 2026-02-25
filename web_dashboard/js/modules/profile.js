// profile.js - Profile management module
class ProfileManager {
    constructor(apiClient) {
        this.api = apiClient;
        this._editBtnInitialized = false;
        this._pendingAvatarFile = null;   // file selected but not yet uploaded
        this._currentProfile = null;      // cached profile data from last load
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
            this._currentProfile = profileData;
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
        // Username
        const displayName = profile.username || 'Player';
        document.getElementById('profileDisplayName').textContent = displayName;
        document.getElementById('profileUsername').textContent = profile.username || '';

        // Avatar — use backend URL if available, otherwise default
        const avatarEl = document.getElementById('profileAvatarLarge');
        if (profile.avatar_url) {
            avatarEl.src = profile.avatar_url;
        } else {
            avatarEl.src = 'assets/players/1000055338.png';
        }

        // Bio
        const bioElement = document.getElementById('userBio');
        if (profile.bio) {
            bioElement.innerHTML = `<p>${this._escapeHtml(profile.bio)}</p>`;
        } else {
            bioElement.innerHTML = '<p class="bio-placeholder">No description yet...</p>';
        }

        // Stats
        const statsEl = document.getElementById('profileStats');
        if (statsEl) {
            statsEl.innerHTML = `
                <div class="stat-card"><span class="stat-value">${profile.total_score ?? 0}</span><span class="stat-label">Total Score</span></div>
                <div class="stat-card"><span class="stat-value">${profile.games_played ?? 0}</span><span class="stat-label">Games Played</span></div>
                <div class="stat-card"><span class="stat-value">${profile.highest_level ?? 1}</span><span class="stat-label">Highest Level</span></div>
                <div class="stat-card"><span class="stat-value">${profile.achievements_count ?? 0}</span><span class="stat-label">Achievements</span></div>
            `;
        }

        // Favorites (future)
        const favoritesGrid = document.getElementById('favoritesGrid');
        if (favoritesGrid) {
            favoritesGrid.innerHTML = '<div class="favorite-item">⭐ Favorites coming soon!</div>';
        }

        // Apply saved background color
        if (profile.bg_color && profile.bg_color !== '#000000') {
            const container = document.querySelector('.profile-container');
            if (container) container.style.backgroundColor = profile.bg_color;
        }
    }

    /** Simple HTML escape to prevent XSS in bio */
    _escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    toggleEditButton(show) {
        const editBtn = document.getElementById('editProfileBtn');
        if (!editBtn) return;
        if (show) {
            editBtn.classList.remove('hidden');
            editBtn.onclick = () => this.openEditModal();
        } else {
            editBtn.classList.add('hidden');
            editBtn.onclick = null;
        }
    }

    openEditModal() {
        const modal = document.getElementById('editProfileModal');
        modal.classList.remove('hidden');
        this._pendingAvatarFile = null;
        
        // Pre-fill with current data
        this.populateEditModal();
        
        // Close handlers (use onclick to avoid stacking listeners)
        modal.querySelector('.modal-close').onclick = () => modal.classList.add('hidden');
        modal.querySelector('.cancel-btn').onclick = () => modal.classList.add('hidden');
        
        // Save handler
        document.getElementById('saveProfileBtn').onclick = () => this.saveProfileChanges();
        
        // Bio character counter
        const bioTextarea = document.getElementById('editBio');
        bioTextarea.oninput = () => {
            document.getElementById('bioCharCount').textContent = bioTextarea.value.length;
        };
        
        // Color selection
        document.querySelectorAll('.color-option').forEach(option => {
            option.onclick = () => {
                document.querySelectorAll('.color-option').forEach(opt => opt.classList.remove('selected'));
                option.classList.add('selected');
            };
        });
        
        // Avatar upload — preview + store file for later upload
        document.getElementById('avatarUpload').onchange = (e) => {
            const file = e.target.files[0];
            if (!file) return;
            if (file.size > 5 * 1024 * 1024) {
                alert('File too big! Max 5MB');
                e.target.value = '';
                return;
            }
            this._pendingAvatarFile = file;
            // Preview
            const reader = new FileReader();
            reader.onload = (ev) => {
                document.getElementById('profileAvatarLarge').src = ev.target.result;
            };
            reader.readAsDataURL(file);
        };
    }

    populateEditModal() {
        const p = this._currentProfile || {};
        
        // Bio
        const bio = p.bio || '';
        document.getElementById('editBio').value = bio;
        document.getElementById('bioCharCount').textContent = bio.length;
        
        // Show scores toggle
        const toggle = document.getElementById('showScoresToggle');
        if (toggle) toggle.checked = p.show_scores !== false;
        
        // Highlight current background color
        const currentBg = p.bg_color || '#000000';
        document.querySelectorAll('.color-option').forEach(opt => {
            opt.classList.toggle('selected', opt.dataset.color === currentBg);
        });
    }

    async saveProfileChanges() {
        const modal = document.getElementById('editProfileModal');
        const saveBtn = document.getElementById('saveProfileBtn');
        
        // Disable button during save
        if (saveBtn) { saveBtn.disabled = true; saveBtn.textContent = 'Saving…'; }
        
        try {
            // 1. Upload avatar if a new file was selected
            if (this._pendingAvatarFile) {
                await this._uploadAvatar(this._pendingAvatarFile);
                this._pendingAvatarFile = null;
            }
            
            // 2. Save text/color fields via PATCH /game/profile/me
            const updates = {
                bio: document.getElementById('editBio').value,
                bg_color: document.querySelector('.color-option.selected')?.dataset.color || '#000000',
                show_scores: document.getElementById('showScoresToggle')?.checked ?? true,
            };
            
            await this.api.request('/game/profile/me', {
                method: 'PATCH',
                body: JSON.stringify(updates)
            });
            
            modal.classList.add('hidden');
            await this.loadProfile(); // Reload profile to reflect changes
            
        } catch (error) {
            console.error('Erreur sauvegarde:', error);
            alert('Error saving changes');
        } finally {
            if (saveBtn) { saveBtn.disabled = false; saveBtn.textContent = 'Save Changes'; }
        }
    }

    async _uploadAvatar(file) {
        const token = localStorage.getItem('access_token');
        const formData = new FormData();
        formData.append('avatar', file);
        
        const response = await fetch('/api/game/profile/me/avatar', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
                // Note: do NOT set Content-Type — browser sets it with boundary for FormData
            },
            body: formData
        });
        
        if (!response.ok) {
            const err = await response.text();
            throw new Error(`Avatar upload failed: ${err}`);
        }
        
        return response.json();
    }

    showPublicProfile(username) {
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
