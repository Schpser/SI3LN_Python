// Dashboard - Script
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 SI3LN Dashboard Loaded');

    updateStatus();
    
    // Leaderboard Loaded
    loadLeaderboard();
    
    // Check API (30sec)
    setInterval(updateStatus, 30000);
});

async function updateStatus() {
    try {
        const response = await fetch('/api/game/stats');
        if (response.ok) {
            document.getElementById('api-status').textContent = '✅ Connected';
            document.getElementById('api-status').style.color = '#00ff00';
        }
    } catch (error) {
        document.getElementById('api-status').textContent = '❌ Outline';
        document.getElementById('api-status').style.color = '#ff4444';
    }
}

async function loadLeaderboard() {
    try {
        const response = await fetch('/api/game/leaderboard');
        const data = await response.json();
        
        const leaderboardDiv = document.getElementById('leaderboard');
        leaderboardDiv.innerHTML = '<ul>' + 
            data.map(score => 
                `<li>${score.player_username}: ${score.score} pts</li>`
            ).join('') + 
            '</ul>';
    } catch (error) {
        console.log('API not available');
    }
}
