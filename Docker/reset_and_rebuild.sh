#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Docker – Full reset and rebuild for SI3LN_Python
#
# What it does:
#   1. Stop and remove all project containers, networks, and named volumes
#   2. Remove project images (forces a clean rebuild)
#   3. Rebuild and restart all services in detached mode
#   4. Show live logs so you can watch the migration run
#
# Usage (from project root):
#   bash Docker/reset_and_rebuild.sh
#
# To also build the Pygbag game (browser version):
#   bash Docker/reset_and_rebuild.sh --with-game
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

COMPOSE="docker compose -f Docker/docker-compose.yml"
WITH_GAME=false

for arg in "$@"; do
    case $arg in
        --with-game) WITH_GAME=true ;;
        *) echo "Unknown option: $arg"; exit 1 ;;
    esac
done

cd "$(dirname "$0")/.."   # always run from project root
echo ""
echo "════════════════════════════════════════════════════"
echo "  SI3LN_Python – Docker full reset"
echo "  Project root: $(pwd)"
echo "════════════════════════════════════════════════════"
echo ""

# ── Step 1: Stop & remove containers, networks, volumes ──────────────────────
echo "▶  Stopping and removing containers, networks and volumes…"
$COMPOSE down -v --remove-orphans 2>/dev/null || true
echo "   Done."
echo ""

# ── Step 2: Remove project images so next build is fully fresh ───────────────
echo "▶  Removing project images (si3ln_python-api, si3ln_python-game-builder)…"
docker rmi si3ln_python-api si3ln_python-game-builder 2>/dev/null || true
echo "   Done (images not found is OK on first run)."
echo ""

# ── Step 3: Build & start core services ──────────────────────────────────────
echo "▶  Building and starting: db, redis, api, frontend…"
$COMPOSE up --build -d
echo ""
echo "   Services launched.  Waiting for API to become healthy…"
echo ""

# ── Step 4: Tail logs until Django finishes migrations ────────────────────────
echo "▶  Live logs (Ctrl-C to stop tailing – containers keep running):"
echo "────────────────────────────────────────────────────"
$COMPOSE logs -f --tail=50 &
LOG_PID=$!

# Poll until the API container health-check turns healthy (max 90 s)
for i in $(seq 1 18); do
    sleep 5
    STATUS=$(docker inspect --format='{{.State.Health.Status}}' \
        "$(docker compose -f Docker/docker-compose.yml ps -q api 2>/dev/null)" 2>/dev/null || echo "waiting")
    if [ "$STATUS" = "healthy" ]; then
        break
    fi
done

kill $LOG_PID 2>/dev/null || true
echo ""
echo "────────────────────────────────────────────────────"
echo ""

# ── Step 5 (optional): Build Pygbag game ─────────────────────────────────────
if [ "$WITH_GAME" = true ]; then
    echo "▶  Building Pygbag game (this takes ~2-3 minutes)…"
    $COMPOSE --profile game up game-builder
    echo "▶  Restarting frontend so nginx picks up the new volume…"
    $COMPOSE restart frontend
    echo "   Game available at: http://localhost/game/"
    echo ""
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo "════════════════════════════════════════════════════"
echo "  All done!  Services:"
echo ""
echo "  Dashboard  →  http://localhost"
echo "  API docs   →  http://localhost:8000/api/docs"
echo "  Django admin → http://localhost:8000/admin/"
if [ "$WITH_GAME" = true ]; then
echo "  Browser game → http://localhost/game/"
fi
echo ""
echo "  Useful commands:"
echo "    $COMPOSE logs -f           # live logs"
echo "    $COMPOSE ps                # container status"
echo "    $COMPOSE down              # stop"
echo ""
echo "  Run API tests (once API is up):"
echo "    python Tests/test_api_endpoints.py"
echo "════════════════════════════════════════════════════"
echo ""
