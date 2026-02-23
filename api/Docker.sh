#!/bin/bash
# entrypoint.sh

echo "🐳 Démarrage en environnement Docker..."

# Migrations
python manage.py migrate

# Create superuser if not exists
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("✅ Admin créé pour Docker !")
EOF

./start_server.sh
