#!/bin/bash
# Script to cleanly start the Django development server

echo "🔍 Checking for running servers..."

if lsof -i :8000 > /dev/null 2>&1; then
    echo "⚠️  Port 8000 in use, cleaning up..."
    lsof -ti :8000 | xargs kill -9 2>/dev/null
    sleep 1
fi

echo "🚀 Starting fresh Django server..."
cd "$(dirname "$0")" || exit 1

python3 manage.py runserver 127.0.0.1:8000
