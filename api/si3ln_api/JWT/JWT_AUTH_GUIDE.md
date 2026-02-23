# 🔐 JWT Authentication Guide - SI3LN API

## ✨ Security Features

Your API now has:
- ✅ **JWT Tokens** with 24-hour expiration
- ✅ **Pepper-enhanced security** (HMAC-SHA256)
- ✅ **Protected endpoints** requiring authentication
- ✅ **Automatic re-login** requirement after 24 hours

## 🔑 How JWT Works

1. **Register/Login** → Get JWT token (valid 24 hours)
2. **Include token** in requests: `Authorization: Bearer <token>`
3. **Token expires** → Must login again after 24 hours
4. **Pepper adds** extra layer of security to token validation

## 🚀 Quick Start

### 1. Configure Security Settings

Create `/home/schpser/SI3LN/api/.env` from `.env.example`:

```bash
cd /home/schpser/SI3LN/api
cp .env.example .env
```

Edit `.env` and change these values:
```env
SECRET_KEY=your-very-secret-key-change-this
JWT_SECRET_KEY=your-jwt-secret-key-different-from-above
JWT_PEPPER=your-pepper-secret-32-chars-minimum
JWT_EXPIRATION_HOURS=24
```

### 2. Install Dependencies & Restart API

```bash
cd /home/schpser/SI3LN/api
pip3 install -r requirements.txt
python3 manage.py runserver
```

## 📡 API Endpoints

### Public Endpoints (No Auth Required)

- `GET /api/game/leaderboard` - View leaderboard
- `GET /api/game/stats` - View statistics
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token

### Protected Endpoints (Auth Required)

All require `Authorization: Bearer <token>` header:

- `GET /api/game/players` - List players
- `GET /api/game/players/{id}` - Get player
- `PUT /api/game/players/{id}` - Update player
- `DELETE /api/game/players/{id}` - Delete player
- `GET /api/game/sessions` - List sessions
- `POST /api/game/sessions` - Create session
- `GET /api/game/sessions/{id}` - Get session
- `PATCH /api/game/sessions/{id}` - Update session
- `DELETE /api/game/sessions/{id}` - Delete session
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/refresh` - Refresh JWT token

## 🎮 Usage Examples

### Register a New User

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "player1",
    "password": "secure_password",
    "email": "player1@si3ln.game"
  }'
```

**Response:**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "username": "player1",
  "player_id": 1
}
```

### Login

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "player1",
    "password": "secure_password"
  }'
```

### Use Token for Protected Endpoints

```bash
# Save token
TOKEN="your_jwt_token_here"

# Create a game session (requires auth)
curl -X POST http://127.0.0.1:8000/api/game/sessions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"player_id": 1}'

# Update session score (requires auth)
curl -X PATCH http://127.0.0.1:8000/api/game/sessions/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "score": 5000,
    "level_reached": 10,
    "enemies_killed": 50
  }'
```

### Check Current User

```bash
curl http://127.0.0.1:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### Refresh Token (Extends 24 hours)

```bash
curl -X POST http://127.0.0.1:8000/api/auth/refresh \
  -H "Authorization: Bearer $TOKEN"
```

## 🎯 C++ Game Integration

The C++ game automatically handles JWT authentication:

```cpp
// Automatic registration and login
apiClient.registerUser("PlayerName", "password", "email@example.com");

// Token is stored and used automatically
if (apiClient.isAuthenticated()) {
    // All API calls now include JWT token
    int sessionId = apiClient.startGameSession(playerId);
    // ...
}

// Logout (clears token)
apiClient.logout();
```

## ⏱️ Token Expiration

- **Tokens expire after 24 hours**
- Game will need to re-authenticate
- Use refresh endpoint to extend without re-login
- Server returns 401 error when token expired

## 🔒 Security Features Explained

### 1. JWT (JSON Web Token)
- Industry-standard token format
- Contains user info + expiration
- Cryptographically signed

### 2. Pepper
- Extra secret added to token validation
- Stored only on server (`JWT_PEPPER`)
- Makes tokens harder to forge
- Uses HMAC-SHA256 hashing

### 3. Token Structure
```
{
  "user_id": 1,
  "username": "player1",
  "player_id": 1,
  "peppered_id": "hash_with_pepper",
  "exp": 1770468000,  // Expiration (24h from creation)
  "iat": 1770381600,  // Issued at
  "type": "access"
}
```

## 🧪 Testing

Run the updated test suite:
```bash
cd /home/schpser/SI3LN/api
python3 test_api_auth.py
```

## ⚠️ Important Notes

1. **Change default secrets** in production
2. **Use HTTPS** in production (JWT over HTTP is insecure)
3. **Store tokens securely** in client
4. **Never commit** `.env` file to git
5. **Tokens expire** - handle 401 errors gracefully

## 🔄 Migration from Old API

If you have existing data without authentication:
1. All players need to register/login
2. Previous sessions remain accessible
3. New sessions require authentication

## 📝 Error Responses

### 401 Unauthorized
```json
{
  "error": "Authentication required"
}
```

```json
{
  "error": "Invalid or expired token. Please login again."
}
```

### 400 Bad Request
```json
{
  "error": "Invalid credentials"
}
```

```json
{
  "error": "Username already exists"
}
```

## 🎉 Benefits

✅ **Secure** - Industry-standard JWT with pepper
✅ **Stateless** - No server-side session storage
✅ **Scalable** - Works across multiple servers
✅ **Time-limited** - Automatic expiration
✅ **Easy to use** - Bearer token in header
✅ **Flexible** - Can refresh without re-login

---

Your API is now production-ready with enterprise-grade security! 🛡️
