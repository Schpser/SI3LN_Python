// game-session.js — Game Session model / entity
// ================================================

'use strict';

class GameSession {
    constructor(data = {}) {
        this.id = data.id || null;
        this.playerId = data.player_id || data.playerId || null;
        this.worldId = data.world_id || data.worldId || null;
        this.score = data.score || 0;
        this.levelReached = data.level_reached || data.levelReached || 1;
        this.startedAt = data.started_at || data.startedAt || new Date().toISOString();
        this.endedAt = data.ended_at || data.endedAt || null;
        this.completed = data.completed || false;
    }

    get duration() {
        if (!this.endedAt) return null;
        const start = new Date(this.startedAt);
        const end = new Date(this.endedAt);
        return Math.round((end - start) / 1000); // seconds
    }

    get isActive() {
        return !this.completed && !this.endedAt;
    }

    get durationFormatted() {
        const d = this.duration;
        if (d === null) return 'In progress';
        const mins = Math.floor(d / 60);
        const secs = d % 60;
        return `${mins}m ${secs}s`;
    }

    toJSON() {
        return {
            id: this.id,
            player_id: this.playerId,
            world_id: this.worldId,
            score: this.score,
            level_reached: this.levelReached,
            started_at: this.startedAt,
            ended_at: this.endedAt,
            completed: this.completed,
        };
    }

    static fromApi(data) {
        return new GameSession(data);
    }
}

window.GameSession = GameSession;
