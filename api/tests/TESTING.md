# API Testing Guide

## Quick Test

Run the comprehensive test suite:

```bash
cd /home/schpser/SI3LN/api
python3 test_api.py
```

## Test Results ✅

All 12 tests passed:
- ✓ Player creation
- ✓ Get all players
- ✓ Get specific player
- ✓ Update player
- ✓ Session creation
- ✓ Get all sessions
- ✓ Get specific session
- ✓ Update session
- ✓ Leaderboard
- ✓ Statistics
- ✓ Delete session
- ✓ Delete player

## Manual Testing with curl

### 1. Create a Player
```bash
curl -X POST http://127.0.0.1:8000/api/game/players \
  -H "Content-Type: application/json" \
  -d '{"username": "TestPlayer", "email": "test@si3ln.game"}'
```

### 2. Get All Players
```bash
curl http://127.0.0.1:8000/api/game/players
```

### 3. Start a Game Session
```bash
curl -X POST http://127.0.0.1:8000/api/game/sessions \
  -H "Content-Type: application/json" \
  -d '{"player_id": 1}'
```

### 4. Update Session Score
```bash
curl -X PATCH http://127.0.0.1:8000/api/game/sessions/1 \
  -H "Content-Type: application/json" \
  -d '{"score": 2000, "level_reached": 10, "enemies_killed": 50}'
```

### 5. Get Leaderboard
```bash
curl http://127.0.0.1:8000/api/game/leaderboard?limit=10
```

### 6. Get Statistics
```bash
curl http://127.0.0.1:8000/api/game/stats
```

## Interactive Testing

Open in your browser:
- **API Docs:** http://127.0.0.1:8000/api/docs
- Click on any endpoint to test it interactively

## Expected Responses

### Player Created
```json
{
  "id": 1,
  "username": "TestPlayer",
  "email": "test@si3ln.game",
  "total_score": 0,
  "games_played": 0,
  "created_at": "2026-02-06T12:00:00"
}
```

### Session Created
```json
{
  "id": 1,
  "player_id": 1,
  "world_id": null,
  "score": 0,
  "level_reached": 1,
  "enemies_killed": 0,
  "duration_seconds": 0,
  "completed": false,
  "started_at": "2026-02-06T12:00:00",
  "ended_at": null
}
```

### Leaderboard
```json
[
  {
    "rank": 1,
    "player_id": 1,
    "player_username": "TestPlayer",
    "score": 2000,
    "level_reached": 10,
    "world_name": null,
    "created_at": "2026-02-06T12:00:00"
  }
]
```

### Statistics
```json
{
  "total_players": 5,
  "total_sessions": 23,
  "total_score": 45000,
  "average_score": 1956.52,
  "highest_score": 5000
}
```

## Troubleshooting

### API not responding?
```bash
# Check if server is running
curl http://127.0.0.1:8000/api/game/stats

# Start the server
cd /home/schpser/SI3LN/api
python3 manage.py runserver
```

### Database issues?
```bash
# Reset database
cd /home/schpser/SI3LN/api
rm db.sqlite3
python3 manage.py migrate
```

### See all endpoints
```bash
# Visit the interactive docs
firefox http://127.0.0.1:8000/api/docs
# or
curl http://127.0.0.1:8000/api/openapi.json | jq
```

## Test from C++ Game

The game automatically calls these endpoints:
1. Creates player on first run
2. Starts session when game begins
3. Updates score every 5 seconds
4. Sends final data on game end

Check the game console for `[API]` messages!
