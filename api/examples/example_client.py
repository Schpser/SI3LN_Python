"""
Example client for SI3LN API
Demonstrates how to interact with the API
"""

import requests
import json


class SI3LNClient:
    """Simple Python client for SI3LN API"""
    
    def __init__(self, base_url="http://localhost:8000/api"):
        self.base_url = base_url
        self.token = None
        self.player_id = None
        
    def register(self, username, password, email=""):
        """Register a new player"""
        response = requests.post(
            f"{self.base_url}/auth/register",
            json={
                "username": username,
                "password": password,
                "email": email
            }
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data['token']
            self.player_id = data['player_id']
            print(f"✅ Registered as {username} (Player ID: {self.player_id})")
            return data
        else:
            print(f"❌ Registration failed: {response.text}")
            return None
    
    def login(self, username, password):
        """Login existing player"""
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={
                "username": username,
                "password": password
            }
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data['token']
            self.player_id = data['player_id']
            print(f"✅ Logged in as {username} (Player ID: {self.player_id})")
            return data
        else:
            print(f"❌ Login failed: {response.text}")
            return None
    
    def get_headers(self):
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def get_worlds(self):
        """Get all available worlds"""
        response = requests.get(f"{self.base_url}/game/worlds")
        if response.status_code == 200:
            worlds = response.json()
            print(f"🌍 Found {len(worlds)} worlds")
            for world in worlds:
                print(f"  - {world['name']}: {world['description']}")
            return worlds
        return None
    
    def start_session(self, world_id=None):
        """Start a new game session"""
        response = requests.post(
            f"{self.base_url}/game/sessions/start?player_id={self.player_id}",
            json={"world_id": world_id, "level_reached": 1},
            headers=self.get_headers()
        )
        if response.status_code == 200:
            session = response.json()
            print(f"🎮 Game session started (ID: {session['id']})")
            return session
        else:
            print(f"❌ Failed to start session: {response.text}")
            return None
    
    def update_session(self, session_id, score, level, enemies, bullets, duration, completed=False):
        """Update game session with stats"""
        response = requests.put(
            f"{self.base_url}/game/sessions/{session_id}",
            json={
                "score": score,
                "level_reached": level,
                "enemies_killed": enemies,
                "bullets_fired": bullets,
                "duration_seconds": duration,
                "completed": completed
            },
            headers=self.get_headers()
        )
        if response.status_code == 200:
            session = response.json()
            print(f"📊 Session updated - Score: {session['score']}, Accuracy: {session['accuracy']:.1f}%")
            return session
        else:
            print(f"❌ Failed to update session: {response.text}")
            return None
    
    def get_leaderboard(self, period="ALL_TIME"):
        """Get leaderboard"""
        response = requests.get(f"{self.base_url}/game/leaderboard/{period}")
        if response.status_code == 200:
            leaderboard = response.json()
            print(f"\n🏆 Leaderboard ({period})")
            print("-" * 50)
            for entry in leaderboard[:10]:
                print(f"#{entry['rank']:2d} {entry['player_username']:20s} {entry['score']:6d} pts")
            return leaderboard
        return None
    
    def get_player_stats(self):
        """Get player statistics"""
        response = requests.get(
            f"{self.base_url}/game/players/{self.player_id}/stats",
            headers=self.get_headers()
        )
        if response.status_code == 200:
            stats = response.json()
            print(f"\n📈 Your Statistics")
            print("-" * 50)
            print(f"Total Games: {stats['total_games']}")
            print(f"Total Score: {stats['total_score']}")
            print(f"Average Score: {stats['average_score']:.0f}")
            print(f"Highest Level: {stats['highest_level']}")
            print(f"Total Enemies Killed: {stats['total_enemies_killed']}")
            print(f"Average Accuracy: {stats['average_accuracy']:.1f}%")
            print(f"Total Playtime: {stats['total_playtime_seconds']}s")
            print(f"Achievements: {stats['achievements_unlocked']}")
            return stats
        return None
    
    def get_achievements(self):
        """Get available achievements"""
        response = requests.get(f"{self.base_url}/game/achievements")
        if response.status_code == 200:
            achievements = response.json()
            print(f"\n🏅 Achievements ({len(achievements)} available)")
            print("-" * 50)
            for ach in achievements:
                print(f"{ach['icon']} {ach['name']}: {ach['description']} ({ach['points']} pts)")
            return achievements
        return None


def main():
    """Example usage of the SI3LN API client"""
    
    client = SI3LNClient()
    
    print("=" * 50)
    print("🎮 SI3LN Game API Client Example")
    print("=" * 50)
    
    # Register or login
    username = "demo_player"
    password = "demo123"
    
    # Try to login first, register if it fails
    if not client.login(username, password):
        client.register(username, password, "demo@example.com")
    
    print("\n")
    
    # Get available worlds
    worlds = client.get_worlds()
    
    print("\n")
    
    # Start a game session
    session = client.start_session(world_id=1 if worlds else None)
    
    if session:
        # Simulate game progress
        import time
        print("\n🎮 Simulating game...")
        time.sleep(1)
        
        # Update with some stats
        client.update_session(
            session_id=session['id'],
            score=1250,
            level=5,
            enemies=42,
            bullets=95,
            duration=180,
            completed=True
        )
    
    print("\n")
    
    # Get player stats
    client.get_player_stats()
    
    print("\n")
    
    # Get leaderboard
    client.get_leaderboard("ALL_TIME")
    
    print("\n")
    
    # Get achievements
    client.get_achievements()
    
    print("\n")
    print("=" * 50)
    print("✨ Demo complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
