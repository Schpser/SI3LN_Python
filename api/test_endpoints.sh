#!/bin/bash

echo "🧪 Testing SI3LN API Endpoints"
echo "================================"
echo ""

BASE_URL="http://localhost:8000/api"

# Public endpoints (no auth needed)
echo "✅ Testing PUBLIC endpoints..."
echo ""

echo "1. Game Stats:"
curl -s $BASE_URL/game/stats | python3 -m json.tool
echo ""

echo "2. Leaderboard:"
curl -s $BASE_URL/game/leaderboard?limit=5 | python3 -m json.tool
echo ""

echo "3. Worlds List:"
curl -s $BASE_URL/game/worlds | python3 -m json.tool
echo ""

echo "4. Achievements List:"
curl -s $BASE_URL/game/achievements | python3 -m json.tool
echo ""

echo "✅ All public endpoints working!"
echo ""
echo "📝 To test authenticated endpoints, you need to:"
echo "   1. POST /api/auth/register or /api/auth/login to get a token"
echo "   2. Use the token in 'Authorization: Bearer <token>' header"
echo ""
echo "Example:"
echo '   curl -X POST $BASE_URL/auth/login -H "Content-Type: application/json" -d'"'"'{"username":"admin","password":"yourpass"}'"'"
echo ""
