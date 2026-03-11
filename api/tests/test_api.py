#!/usr/bin/env python3
"""
Test script for SI3LN Django Ninja API with JWT Authentication
Tests all endpoints including authentication flow
"""

import requests
import json
from datetime import datetime
import sys

# API Base URLs
BASE_URL = "http://127.0.0.1:8000/api"
AUTH_URL = f"{BASE_URL}/auth"
GAME_URL = f"{BASE_URL}/game"

# Global token storage
jwt_token = None

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")

def test_api_connection():
    """Test if API server is reachable"""
    print_info("Testing API connection...")
    try:
        response = requests.get(f"{GAME_URL}/stats", timeout=5)
        if response.status_code in [200, 404]:
            print_success("API server is reachable")
            return True
        else:
            print_error(f"API returned unexpected status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to API server. Is it running?")
        print_info("Start it with: cd api && python3 manage.py runserver")
        return False
    except Exception as e:
        print_error(f"Connection error: {str(e)}")
        return False

def test_register():
    """Test user registration and get JWT token"""
    global jwt_token
    print_info("Testing user registration...")
    
    timestamp = datetime.now().timestamp()
    user_data = {
        "username": f"testuser_{timestamp}",
        "password": f"testpass_{timestamp}",
        "email": f"test_{timestamp}@si3ln.game"
    }
    
    try:
        response = requests.post(f"{AUTH_URL}/register", json=user_data)
        
        if response.status_code == 200:
            data = response.json()
            jwt_token = data['token']
            print_success(f"User registered: {data['username']}, Player ID: {data['player_id']}")
            print_info(f"JWT token received (expires in 24 hours)")
            return data['player_id']
        else:
            print_error(f"Failed to register: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error registering: {str(e)}")
        return None

def test_login():
    """Test user login"""
    global jwt_token
    print_info("Testing user login...")
    
    # Register a user first
    timestamp = datetime.now().timestamp()
    register_data = {
        "username": f"logintest_{timestamp}",
        "password": "testpassword",
        "email": f"login_{timestamp}@si3ln.game"
    }
    
    requests.post(f"{AUTH_URL}/register", json=register_data)
    
    # Now login
    login_data = {
        "username": register_data["username"],
        "password": register_data["password"]
    }
    
    try:
        response = requests.post(f"{AUTH_URL}/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            jwt_token = data['token']
            print_success(f"Login successful: {data['username']}")
            return True
        else:
            print_error(f"Failed to login: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error logging in: {str(e)}")
        return False

def get_auth_headers():
    """Get authorization headers with JWT token"""
    return {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }

def test_get_current_user():
    """Test getting current user info"""
    print_info("Testing get current user...")
    
    try:
        response = requests.get(f"{AUTH_URL}/me", headers=get_auth_headers())
        
        if response.status_code == 200:
            user = response.json()
            print_success(f"Current user: {user['username']}")
            return True
        else:
            print_error(f"Failed to get current user: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error getting current user: {str(e)}")
        return False

def test_create_player():
    """Test creating a new player"""
    print_info("Testing player creation...")
    
    player_data = {
        "username": f"TestPlayer_{datetime.now().timestamp()}",
        "email": f"test_{datetime.now().timestamp()}@si3ln.game"
    }
    
    try:
        response = requests.post(f"{GAME_URL}/players", json=player_data)
        
        if response.status_code == 200:
            player = response.json()
            print_success(f"Player created: ID={player['id']}, Username={player['username']}")
            return player['id']
        else:
            print_error(f"Failed to create player: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error creating player: {str(e)}")
        return None

def test_get_players():
    """Test getting all players (requires auth)"""
    print_info("Testing get all players...")
    
    try:
        # basic listing
        response = requests.get(f"{GAME_URL}/players", headers=get_auth_headers())
        if response.status_code == 200:
            players = response.json()
            print_success(f"Retrieved {len(players)} players")
            if players:
                print_info(f"Sample: {players[0]['username']}")
        else:
            print_error(f"Failed to get players: {response.status_code}")
            return False

        # pagination: limit=1 should return at most one
        response = requests.get(
            f"{GAME_URL}/players?limit=1&offset=0", headers=get_auth_headers()
        )
        if response.status_code == 200 and len(response.json()) <= 1:
            print_success("Pagination (limit=1) works")
        else:
            print_error("Pagination test failed")
            return False

        return True
    except Exception as e:
        print_error(f"Error getting players: {str(e)}")
        return False

def test_get_player(player_id):
    """Test getting a specific player (requires auth)"""
    print_info(f"Testing get player ID {player_id}...")
    
    try:
        response = requests.get(f"{GAME_URL}/players/{player_id}", headers=get_auth_headers())
        
        if response.status_code == 200:
            player = response.json()
            print_success(f"Retrieved player: {player['username']}")
            return True
        else:
            print_error(f"Failed to get player: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error getting player: {str(e)}")
        return False

def test_update_player(player_id):
    """Test updating a player"""
    print_info(f"Testing update player ID {player_id}...")
    
    update_data = {
        "username": f"UpdatedPlayer_{datetime.now().timestamp()}",
        "email": f"updated_{datetime.now().timestamp()}@si3ln.game"
    }
    
    try:
        response = requests.put(f"{GAME_URL}/players/{player_id}", json=update_data, headers=get_auth_headers())
        
        if response.status_code == 200:
            player = response.json()
            print_success(f"Player updated: {player['username']}")
            return True
        else:
            print_error(f"Failed to update player: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error updating player: {str(e)}")
        return False

def test_create_session(player_id):
    """Test creating a game session"""
    print_info(f"Testing session creation for player {player_id}...")
    
    session_data = {
        "player_id": player_id,
        "world_id": None
    }
    
    try:
        response = requests.post(f"{GAME_URL}/sessions", json=session_data, headers=get_auth_headers())
        
        if response.status_code == 200:
            session = response.json()
            print_success(f"Session created: ID={session['id']}")
            return session['id']
        else:
            print_error(f"Failed to create session: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error creating session: {str(e)}")
        return None

def test_get_sessions():
    """Test getting all sessions"""
    print_info("Testing get all sessions...")
    
    try:
        response = requests.get(f"{GAME_URL}/sessions", headers=get_auth_headers())
        
        if response.status_code == 200:
            sessions = response.json()
            print_success(f"Retrieved {len(sessions)} sessions")
            if sessions:
                print_info(f"Latest session score: {sessions[0]['score']}")
        else:
            print_error(f"Failed to get sessions: {response.status_code}")
            return False

        # pagination sanity check
        response = requests.get(
            f"{GAME_URL}/sessions?limit=1&offset=0", headers=get_auth_headers()
        )
        if response.status_code == 200 and len(response.json()) <= 1:
            print_success("Session pagination works")
        else:
            print_error("Session pagination test failed")
            return False

        return True
    except Exception as e:
        print_error(f"Error getting sessions: {str(e)}")
        return False

def test_get_session(session_id):
    """Test getting a specific session"""
    print_info(f"Testing get session ID {session_id}...")
    
    try:
        response = requests.get(f"{GAME_URL}/sessions/{session_id}", headers=get_auth_headers())
        
        if response.status_code == 200:
            session = response.json()
            print_success(f"Retrieved session: Score={session['score']}")
            return True
        else:
            print_error(f"Failed to get session: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error getting session: {str(e)}")
        return False

def test_update_session(session_id):
    """Test updating a game session"""
    print_info(f"Testing update session ID {session_id}...")
    
    update_data = {
        "score": 1500,
        "level_reached": 5,
        "enemies_killed": 45,
        "duration_seconds": 180
    }
    
    try:
        response = requests.patch(f"{GAME_URL}/sessions/{session_id}", json=update_data, headers=get_auth_headers())
        
        if response.status_code == 200:
            session = response.json()
            print_success(f"Session updated: Score={session['score']}, Level={session['level_reached']}")
            return True
        else:
            print_error(f"Failed to update session: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error updating session: {str(e)}")
        return False

def test_get_leaderboard():
    """Test getting the leaderboard"""
    print_info("Testing get leaderboard...")
    
    try:
        response = requests.get(f"{GAME_URL}/leaderboard?limit=5")
        
        if response.status_code == 200:
            leaderboard = response.json()
            print_success(f"Retrieved leaderboard with {len(leaderboard)} entries")
            for entry in leaderboard[:3]:
                print_info(f"  #{entry['rank']}: {entry['player_username']} - {entry['score']} points")
            return True
        else:
            print_error(f"Failed to get leaderboard: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error getting leaderboard: {str(e)}")
        return False

def test_get_stats():
    """Test getting game statistics"""
    print_info("Testing get statistics...")
    
    try:
        response = requests.get(f"{GAME_URL}/stats")
        
        if response.status_code == 200:
            stats = response.json()
            print_success("Retrieved game statistics:")
            print_info(f"  Total Players: {stats.get('total_players', 0)}")
            print_info(f"  Total Sessions: {stats.get('total_sessions', 0)}")
            print_info(f"  Total Score: {stats.get('total_score', 0)}")
            print_info(f"  Average Score: {stats.get('average_score', 0)}")
            print_info(f"  Highest Score: {stats.get('highest_score', 0)}")
            return True
        else:
            print_error(f"Failed to get stats: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error getting stats: {str(e)}")
        return False

def test_delete_session(session_id):
    """Test deleting a session"""
    print_info(f"Testing delete session ID {session_id}...")
    
    try:
        response = requests.delete(f"{GAME_URL}/sessions/{session_id}", headers=get_auth_headers())
        
        if response.status_code == 200:
            print_success("Session deleted successfully")
            return True
        else:
            print_error(f"Failed to delete session: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error deleting session: {str(e)}")
        return False

def test_delete_player(player_id):
    """Test deleting a player"""
    print_info(f"Testing delete player ID {player_id}...")
    
    try:
        response = requests.delete(f"{GAME_URL}/players/{player_id}", headers=get_auth_headers())
        
        if response.status_code == 200:
            print_success("Player deleted successfully")
            return True
        else:
            print_error(f"Failed to delete player: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error deleting player: {str(e)}")
        return False

def run_all_tests():
    """Run all API tests"""
    print("\n" + "="*60)
    print(f"{Colors.BLUE}SI3LN Django Ninja API Test Suite (JWT Auth){Colors.RESET}")
    print("="*60 + "\n")
    
    # Track results
    passed = 0
    failed = 0
    
    # Test connection
    if not test_api_connection():
        print_error("\nAPI server is not running. Please start it first.")
        return
    
    print("\n" + "-"*60)
    print("AUTHENTICATION ENDPOINTS")
    print("-"*60)
    
    # Register user and get token
    player_id = test_register()
    if player_id:
        passed += 1
    else:
        failed += 1
        print_error("\nCannot continue without authentication")
        return
    
    # Test login
    if test_login():
        passed += 1
    else:
        failed += 1
    
    # Test get current user
    if test_get_current_user():
        passed += 1
    else:
        failed += 1
    
    print("\n" + "-"*60)
    print("PLAYER ENDPOINTS (AUTHENTICATED)")
    print("-"*60)
    
    # Get all players
    if test_get_players():
        passed += 1
    else:
        failed += 1
    
    # Get specific player
    if test_get_player(player_id):
        passed += 1
    else:
        failed += 1
    
    # Update player
    if test_update_player(player_id):
        passed += 1
    else:
        failed += 1
    
    print("\n" + "-"*60)
    print("GAME SESSION ENDPOINTS")
    print("-"*60)
    
    # Create session
    session_id = test_create_session(player_id)
    if session_id:
        passed += 1
    else:
        failed += 1
        session_id = None
    
    # Get all sessions
    if test_get_sessions():
        passed += 1
    else:
        failed += 1
    
    if session_id:
        # Get specific session
        if test_get_session(session_id):
            passed += 1
        else:
            failed += 1
        
        # Update session
        if test_update_session(session_id):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "-"*60)
    print("LEADERBOARD & STATS ENDPOINTS")
    print("-"*60)
    
    # Get leaderboard
    if test_get_leaderboard():
        passed += 1
    else:
        failed += 1
    
    # Get stats
    if test_get_stats():
        passed += 1
    else:
        failed += 1
    
    print("\n" + "-"*60)
    print("CLEANUP (DELETE ENDPOINTS)")
    print("-"*60)
    
    # Delete session
    if session_id and test_delete_session(session_id):
        passed += 1
    else:
        failed += 1
    
    # Delete player
    if test_delete_player(player_id):
        passed += 1
    else:
        failed += 1
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    total = passed + failed
    print_success(f"Passed: {passed}/{total}")
    if failed > 0:
        print_error(f"Failed: {failed}/{total}")
    else:
        print_success("All tests passed! 🎉")
    print("="*60 + "\n")
    
    return failed == 0

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_warning("\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nUnexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
