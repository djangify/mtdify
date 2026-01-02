from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from bookkeeping.services import run_recurring_for_user

User = get_user_model()


class Command(BaseCommand):
    help = "Process recurring entries for all users (or a specific user) and catch up on missed entries."

    def add_arguments(self, parser):
        parser.add_argument(
            "--user",
            type=str,
            help="Email of specific user to process (optional)",
        )

    def handle(self, *args, **options):
        user_email = options.get("user")

        if user_email:
            try:
                user = User.objects.get(email=user_email)
                users = [user]
                self.stdout.write(f"Processing recurring entries for {user.email}...")
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"User with email '{user_email}' not found.")
                )
                return
        else:
            users = User.objects.all()
            self.stdout.write(
                f"Processing recurring entries for all {users.count()} users..."
            )

        total_processed = 0

        for user in users:
            self.stdout.write(f"\n--- Processing user: {user.email} ---")

            results = run_recurring_for_user(user)

            if results:
                for result in results:
                    self.stdout.write(self.style.SUCCESS(f"  ✓ {result}"))
                total_processed += len(results)
            else:
                self.stdout.write("  No recurring entries due for this user.")

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Complete! Processed {total_processed} recurring entries total."
            )
        )
