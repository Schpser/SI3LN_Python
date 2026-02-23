from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Interactively delete a superuser. "
        "If no username is given the command will list superusers and prompt for a choice."
    )

    def add_arguments(self, parser):
        parser.add_argument("username", nargs="?", help="username to delete")
        parser.add_argument(
            "--no-input",
            action="store_true",
            dest="no_input",
            help="do not prompt for confirmation (requires username)",
        )

    def handle(self, *args, **options):
        username = options.get("username")
        no_input = options.get("no_input")

        # --no-input requires a username
        if no_input and not username:
            raise CommandError("When using --no-input you must provide a username")

        # Resolve target user (interactive selection if username not provided)
        if username:
            try:
                target = User.objects.get(username=username)
            except User.DoesNotExist:
                raise CommandError(f"User '{username}' not found")
            if not target.is_superuser:
                raise CommandError(f"User '{username}' is not a superuser")
        else:
            super_qs = list(User.objects.filter(is_superuser=True).order_by("id"))
            if not super_qs:
                raise CommandError("No superusers found")

            self.stdout.write("Superusers:")
            for idx, u in enumerate(super_qs, start=1):
                self.stdout.write(f"  {idx}) {u.username} (id={u.id})")

            choice = input("Enter number or username to delete (empty to abort): ").strip()
            if not choice:
                self.stdout.write(self.style.WARNING("Aborted"))
                return

            if choice.isdigit():
                idx = int(choice)
                if idx < 1 or idx > len(super_qs):
                    raise CommandError("Invalid selection")
                target = super_qs[idx - 1]
            else:
                try:
                    target = User.objects.get(username=choice)
                except User.DoesNotExist:
                    raise CommandError(f"User '{choice}' not found")
                if not target.is_superuser:
                    raise CommandError(f"User '{choice}' is not a superuser")

        # Safety checks
        if target.is_superuser:
            su_count = User.objects.filter(is_superuser=True).count()
            if su_count <= 1:
                raise CommandError("Refuse to delete the last superuser")

        # Confirmation (unless --no-input)
        if not no_input:
            confirm = input(f"Type 'yes' to confirm deletion of superuser '{target.username}': ").strip().lower()
            if confirm != "yes":
                self.stdout.write(self.style.WARNING("Aborted"))
                return

        target.delete()
        self.stdout.write(self.style.SUCCESS(f"User '{target.username}' deleted"))
