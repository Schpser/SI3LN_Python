// game.js — Game entity model
// ============================

'use strict';

class GameEntity {
    constructor(data = {}) {
        this.id = data.id || '';
        this.name = data.name || '';
        this.description = data.description || '';
        this.url = data.url || '';
        this.thumbnail = data.thumbnail || '';
        this.comingSoon = data.comingSoon || false;
        this.homepageBg = data.homepageBg || '#000428';  // Background color for game frame
        this.homepageImage = data.homepageImage || '';     // Background image URL
    }

    get isPlayable() {
        return !this.comingSoon && !!this.url;
    }

    get displayStatus() {
        return this.comingSoon ? 'Coming Soon' : 'Available';
    }

    static catalog() {
        return [
            new GameEntity({
                id: 'si3ln',
                name: 'SI3LN',
                description: 'Space Invaders III Last Night',
                url: 'game/index.html',
                thumbnail: 'assets/worlds/home_page.jpg',
                homepageBg: '#000428',
                homepageImage: 'assets/worlds/home_page.jpg',
            }),
            new GameEntity({
                id: 'game2',
                name: '...',
                description: 'Coming Soon',
                comingSoon: true,
            }),
            new GameEntity({
                id: 'game3',
                name: '...',
                description: 'Coming Soon',
                comingSoon: true,
            }),
        ];
    }

    static findById(id) {
        return GameEntity.catalog().find(g => g.id === id) || null;
    }
}

window.GameEntity = GameEntity;
