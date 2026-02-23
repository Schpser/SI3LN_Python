#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import signal


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n🛑 Shutting down server gracefully...")
    sys.exit(0)


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'si3ln_api.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    if 'runserver' in sys.argv:
        # Register signal handler for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Print info message instead of trying to open browser (WSL doesn't support GUI browsers)
        print("📚 API Docs: http://127.0.0.1:8000/api/docs")
        print("🔧 Admin Panel: http://127.0.0.1:8000/admin")

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
