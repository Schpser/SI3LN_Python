// player.js — Player model / entity
// ===================================

'use strict';

class Player {
    constructor(data = {}) {
        this.id = data.id || null;
        this.username = data.username || '';
        this.email = data.email || '';
        this.bio = data.bio || '';
        this.avatarUrl = data.avatar_url || data.avatarUrl || '';
        this.bgColor = data.bg_color || data.bgColor || '#000000';
        this.totalScore = data.total_score || data.totalScore || 0;
        this.gamesPlayed = data.games_played || data.gamesPlayed || 0;
        this.highestLevel = data.highest_level || data.highestLevel || 1;
        this.achievementsCount = data.achievements_count || data.achievementsCount || 0;
        this.showScores = data.show_scores !== undefined ? data.show_scores : true;
        this.createdAt = data.created_at || data.createdAt || null;
        this.role = data.role || 'player';
    }

    get displayName() {
        return this.username || 'Player';
    }

    get defaultAvatar() {
        return 'assets/players/1000055338.png';
    }

    get avatarSrc() {
        return this.avatarUrl || this.defaultAvatar;
    }

    get isGuest() {
        return !this.id;
    }

    toJSON() {
        return {
            id: this.id,
            username: this.username,
            bio: this.bio,
            avatar_url: this.avatarUrl,
            bg_color: this.bgColor,
            total_score: this.totalScore,
            games_played: this.gamesPlayed,
            highest_level: this.highestLevel,
            show_scores: this.showScores,
        };
    }

    static fromApi(data) {
        return new Player(data);
    }

    static guest() {
        return new Player({ username: 'Guest', role: 'guest' });
    }
}

window.Player = Player;
