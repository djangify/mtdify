from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError
from datetime import datetime, timedelta
from pathlib import Path
import shutil
import sys


class BookkeepingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bookkeeping"

    def get_database_path(self):
        """
        Return the path to the SQLite database file.

        Uses Django's settings to get the actual database location,
        which works correctly for both PyInstaller and Docker/self-hosted.
        """
        from django.conf import settings

        # Get database path from Django settings
        db_settings = settings.DATABASES.get("default", {})
        db_name = db_settings.get("NAME")

        if db_name:
            return Path(db_name)

        # Fallback for legacy PyInstaller builds
        if hasattr(sys, "_MEIPASS") or getattr(sys, "frozen", False):
            return Path(sys.executable).parent / "db.sqlite3"

        return settings.BASE_DIR / "db.sqlite3"

    def get_backup_dir(self):
        """
        Return the directory where backups should be stored.

        Places backups in a 'backups' folder alongside the database.
        """
        db_path = self.get_database_path()
        return db_path.parent / "backups"

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
            DB_PATH = self.get_database_path()
            BACKUP_DIR = self.get_backup_dir()

            BACKUP_DIR.mkdir(parents=True, exist_ok=True)

            if not DB_PATH.exists():
                print(f"⚠️ No database file found at {DB_PATH}. Backup skipped.")
                return

            # Check if database is empty before backing up
            if DB_PATH.stat().st_size == 0:
                print("Database file is empty (0 KB). Backup skipped.")
                return

            timestamp = datetime.now().strftime("%Y-%m-%d")
            backup_file = BACKUP_DIR / f"db-{timestamp}.sqlite3"

            if backup_file.exists():
                print(f"Backup already exists for today: {backup_file.name}")
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
                    print(f"Deleted old backup: {backup_file.name}")

            except Exception:
                continue
