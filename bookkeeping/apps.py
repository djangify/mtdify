from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError
from datetime import datetime, timedelta
from pathlib import Path
import shutil
import sys


class BookkeepingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bookkeeping"

    def get_user_data_dir(self):
        """
        Return the directory where persistent user data should be stored.

        - When running as a PyInstaller .exe:
            Return the folder where the .exe is located.
        - When running in development:
            Return Django's BASE_DIR.
        """
        if hasattr(sys, "_MEIPASS") or getattr(sys, "frozen", False):
            # Running as compiled EXE - return folder containing the .exe
            return Path(sys.executable).parent

        # Running in development - return project root
        from django.conf import settings

        return settings.BASE_DIR

    def ready(self):
        """
        Called when Django starts — seed categories + run backup.
        Prevent backup from running during PyInstaller analysis.
        """
        # --- IMPORTANT: DO NOT RUN BACKUPS DURING PYINSTALLER BUILD ---
        if "pyinstaller" in sys.argv[0].lower():
            return

        # 1. Run backup once at startup
        self.run_daily_backup()

        # 2. Seed categories
        self.seed_default_categories()

    def seed_default_categories(self):
        """Existing category seeding logic, unchanged."""
        from .models import Category

        default_expense_categories = [
            "Advertising & Marketing",
            "Bank Charges",
            "Car/Vehicle Expenses",
            "Cost of Goods Sold",
            "Insurance",
            "Interest & Finance Charges",
            "Legal & Professional Fees",
            "Office Costs",
            "Other Business Expenses",
            "Premises Running Costs",
            "Repairs & Maintenance",
            "Staff Costs",
            "Subcontractor Costs",
            "Telephone, Mobile & Internet",
            "Travel & Subsistence",
            "Utilities",
            "Capital Allowances",
            "Computers & Laptops",
            "Tools & Equipment",
            "Plant & Machinery",
        ]

        default_income_categories = [
            "Turnover - Sales",
            "Other Business Income",
            "Bank Interest",
        ]

        try:
            for name in default_expense_categories:
                Category.objects.get_or_create(
                    name=name,
                    category_type="expense",
                )

            for name in default_income_categories:
                Category.objects.get_or_create(
                    name=name,
                    category_type="income",
                )

        except (OperationalError, ProgrammingError):
            pass

    def run_daily_backup(self):
        """
        Create a daily backup of the database on Django startup.
        Already protected from running during PyInstaller by ready().
        """
        try:
            USER_DIR = self.get_user_data_dir()

            DB_PATH = USER_DIR / "db.sqlite3"
            BACKUP_DIR = USER_DIR / "backups"

            BACKUP_DIR.mkdir(exist_ok=True)

            if not DB_PATH.exists():
                print("⚠️  No database file found. Backup skipped.")
                return

            # ✅ FIX: Check if database is empty before backing up
            if DB_PATH.stat().st_size == 0:
                print("⚠️  Database file is empty (0 KB). Backup skipped.")
                return

            timestamp = datetime.now().strftime("%Y-%m-%d")
            backup_file = BACKUP_DIR / f"db-{timestamp}.sqlite3"

            if backup_file.exists():
                print(f"✅ Backup already exists for today: {backup_file.name}")
                return

            shutil.copy(DB_PATH, backup_file)
            print(f"✅ Backup created: {backup_file.name}")

            self.cleanup_old_backups(BACKUP_DIR, days_to_keep=90)

        except Exception as e:
            print(f"⚠️  Backup failed: {e}")

    def cleanup_old_backups(self, backup_dir, days_to_keep=90):
        """Remove backups older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        for backup_file in backup_dir.glob("db-*.sqlite3"):
            try:
                date_str = backup_file.stem.replace("db-", "")
                file_date = datetime.strptime(date_str, "%Y-%m-%d")

                if file_date < cutoff_date:
                    backup_file.unlink()
                    print(f"🗑️  Deleted old backup: {backup_file.name}")

            except Exception:
                continue
