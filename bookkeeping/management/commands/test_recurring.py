from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from bookkeeping.models import RecurringEntry, Income, Expense
from datetime import datetime, date

User = get_user_model()


class Command(BaseCommand):
    help = "Simulate recurring entry processing without writing records."

    def add_arguments(self, parser):
        parser.add_argument("--date", type=str, help="Run date YYYY-MM-DD")

    def handle(self, *args, **options):
        run_date = (
            datetime.strptime(options["date"], "%Y-%m-%d").date()
            if options["date"]
            else date.today()
        )

        self.stdout.write("")
        self.stdout.write(f"=== Simulation for {run_date} ===")

        entries = RecurringEntry.objects.all()

        for entry in entries:
            next_run = entry.next_run

            # If missing, initialise it properly
            if next_run is None:
                next_run = entry.start_date

            # Advance next_run until it is >= run_date
            while next_run < run_date:
                # Compute next month
                year = next_run.year
                month = next_run.month + 1
                if month > 12:
                    month = 1
                    year += 1

                next_run = date(year, month, entry.day_of_month)

            # Print result
            if next_run == run_date:
                self.stdout.write(f"[PROCESS] {entry.description} – would run today")
            else:
                self.stdout.write(f"[SKIP] {entry.description} – next_run={next_run}")

        self.stdout.write("\nSimulation complete.")
