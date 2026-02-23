#!/bin/bash
set -e

echo "Starting SI3LN API in Docker..."

# ── Wait for database ────────────────────────────────────────────────────────
if [ -n "$DATABASE_URL" ]; then
    echo "Waiting for database..."

    DB_HOST=$(echo "$DATABASE_URL" | sed -E 's|.*@([^:/]+).*|\1|')
    DB_PORT=$(echo "$DATABASE_URL" | sed -E 's|.*:([0-9]+)/[^/].*|\1|')

    echo "  Host: $DB_HOST  Port: $DB_PORT"

    MAX_RETRIES=60
    COUNT=0
    until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U si3ln_user > /dev/null 2>&1; do
        COUNT=$((COUNT + 1))
        if [ "$COUNT" -ge "$MAX_RETRIES" ]; then
            echo "ERROR: Database did not become ready after ${MAX_RETRIES}s. Aborting."
            exit 1
        fi
        echo "  [${COUNT}/${MAX_RETRIES}] Database unavailable - retrying in 1s..."
        sleep 1
    done

    echo "  Database is ready!"
fi

# ── Run migrations ────────────────────────────────────────────────────────────
echo "Running database migrations..."
python manage.py migrate --noinput

# ── Collect static files ──────────────────────────────────────────────────────
echo "Collecting static files..."
python manage.py collectstatic --noinput || true

# ── Create superuser if missing ───────────────────────────────────────────────
echo "Creating superuser if needed..."
python manage.py shell << 'PYEOF'
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@si3ln.local', 'admin123')
    print("Superuser 'admin' created (password: admin123)")
else:
    print("Superuser already exists")
PYEOF

echo ""
echo "========================================"
echo "  SI3LN API starting on port 8000"
echo "  Docs:  http://localhost:8000/api/docs"
echo "  Admin: http://localhost:8000/admin"
echo "         login: admin / admin123"
echo "========================================"
echo ""

exec gunicorn si3ln_api.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
