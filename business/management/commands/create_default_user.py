# business/management/commands/create_default_user.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings


class Command(BaseCommand):
    help = "Create the default demo user if it does not exist."

    def handle(self, *args, **options):
        User = get_user_model()
        email = getattr(settings, "DEFAULT_USER_EMAIL", "demo@example.com")
        password = getattr(settings, "DEFAULT_USER_PASSWORD", "demo123")

        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.NOTICE(f"Default user already exists: {email}")
            )
            return

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name="Demo",
            last_name="User",
            is_staff=True,  # can access admin
            is_superuser=True,  # full control (local app, so it’s fine)
        )
        self.stdout.write(
            self.style.SUCCESS(f"Created default user: {email} / {password}")
        )
