# Save this as: bookkeeping/management/commands/check_2024_data.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from bookkeeping.models import Income, Expense
from bookkeeping.utils import get_tax_year_from_date, get_available_tax_years
from datetime import date

User = get_user_model()


class Command(BaseCommand):
    help = "Check for 2024 data in the database"

    def handle(self, *args, **options):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("CHECKING FOR 2024 DATA")
        self.stdout.write("=" * 60 + "\n")

        # Get first user (assuming demo user)
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR("No users found in database!"))
            return

        self.stdout.write(f"Checking data for user: {user.email}\n")

        # Check Income records
        self.stdout.write("-" * 60)
        self.stdout.write("INCOME RECORDS:")
        self.stdout.write("-" * 60)

        all_income = Income.objects.filter(user=user).order_by("date")
        self.stdout.write(f"Total income records: {all_income.count()}\n")

        if all_income.exists():
            # Show all income with dates and calculated tax years
            for income in all_income:
                tax_year = get_tax_year_from_date(income.date)
                self.stdout.write(
                    f"  Date: {income.date} | Amount: £{income.amount} | "
                    f"Quarter: {income.quarter} | Tax Year: {tax_year} | "
                    f"Desc: {income.description[:30]}"
                )

            # Count by year
            self.stdout.write("\nIncome by calendar year:")
            for year in [2023, 2024, 2025]:
                start = date(year, 1, 1)
                end = date(year, 12, 31)
                count = Income.objects.filter(
                    user=user, date__gte=start, date__lte=end
                ).count()
                if count > 0:
                    self.stdout.write(f"  {year}: {count} records")

            # Count by tax year
            self.stdout.write("\nIncome by TAX year:")
            for tax_year in ["2023-2024", "2024-2025"]:
                start_year = int(tax_year.split("-")[0])
                start = date(start_year, 4, 6)
                end = date(start_year + 1, 4, 5)
                count = Income.objects.filter(
                    user=user, date__gte=start, date__lte=end
                ).count()
                if count > 0:
                    self.stdout.write(f"  {tax_year}: {count} records")

        else:
            self.stdout.write(self.style.WARNING("  No income records found!"))

        # Check Expense records
        self.stdout.write("\n" + "-" * 60)
        self.stdout.write("EXPENSE RECORDS:")
        self.stdout.write("-" * 60)

        all_expenses = Expense.objects.filter(user=user).order_by("date")
        self.stdout.write(f"Total expense records: {all_expenses.count()}\n")

        if all_expenses.exists():
            # Show all expenses with dates and calculated tax years
            for expense in all_expenses:
                tax_year = get_tax_year_from_date(expense.date)
                self.stdout.write(
                    f"  Date: {expense.date} | Amount: £{expense.amount} | "
                    f"Quarter: {expense.quarter} | Tax Year: {tax_year} | "
                    f"Desc: {expense.description[:30]}"
                )

            # Count by year
            self.stdout.write("\nExpenses by calendar year:")
            for year in [2023, 2024, 2025]:
                start = date(year, 1, 1)
                end = date(year, 12, 31)
                count = Expense.objects.filter(
                    user=user, date__gte=start, date__lte=end
                ).count()
                if count > 0:
                    self.stdout.write(f"  {year}: {count} records")

            # Count by tax year
            self.stdout.write("\nExpenses by TAX year:")
            for tax_year in ["2023-2024", "2024-2025"]:
                start_year = int(tax_year.split("-")[0])
                start = date(start_year, 4, 6)
                end = date(start_year + 1, 4, 5)
                count = Expense.objects.filter(
                    user=user, date__gte=start, date__lte=end
                ).count()
                if count > 0:
                    self.stdout.write(f"  {tax_year}: {count} records")

        else:
            self.stdout.write(self.style.WARNING("  No expense records found!"))

        # Check what get_available_tax_years returns
        self.stdout.write("\n" + "-" * 60)
        self.stdout.write("AVAILABLE TAX YEARS (from utils function):")
        self.stdout.write("-" * 60)

        available_years = get_available_tax_years(user)
        if available_years:
            for year in available_years:
                self.stdout.write(f"  ✓ {year}")
        else:
            self.stdout.write(
                self.style.WARNING(
                    "  No tax years returned by get_available_tax_years()"
                )
            )

        # Check earliest and latest dates
        self.stdout.write("\n" + "-" * 60)
        self.stdout.write("DATE RANGE:")
        self.stdout.write("-" * 60)

        if all_income.exists():
            earliest_income = all_income.first().date
            latest_income = all_income.last().date
            self.stdout.write(f"Income: {earliest_income} to {latest_income}")

        if all_expenses.exists():
            earliest_expense = all_expenses.first().date
            latest_expense = all_expenses.last().date
            self.stdout.write(f"Expenses: {earliest_expense} to {latest_expense}")

        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("SUMMARY:")
        self.stdout.write("=" * 60)

        # Check for 2024 data specifically
        year_2024_start = date(2024, 1, 1)
        year_2024_end = date(2024, 12, 31)

        income_2024 = Income.objects.filter(
            user=user, date__gte=year_2024_start, date__lte=year_2024_end
        ).count()

        expense_2024 = Expense.objects.filter(
            user=user, date__gte=year_2024_start, date__lte=year_2024_end
        ).count()

        if income_2024 > 0 or expense_2024 > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✓ YES - Found {income_2024} income and {expense_2024} expense records in 2024"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING("\n✗ NO - No records found in calendar year 2024")
            )

        # Check for tax year 2023-2024 (Apr 6 2023 to Apr 5 2024)
        tax_2023_start = date(2023, 4, 6)
        tax_2023_end = date(2024, 4, 5)

        income_tax_2023 = Income.objects.filter(
            user=user, date__gte=tax_2023_start, date__lte=tax_2023_end
        ).count()

        expense_tax_2023 = Expense.objects.filter(
            user=user, date__gte=tax_2023_start, date__lte=tax_2023_end
        ).count()

        if income_tax_2023 > 0 or expense_tax_2023 > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✓ YES - Found {income_tax_2023} income and {expense_tax_2023} expense records in tax year 2023-2024"
                )
            )

        # Check for tax year 2024-2025 (Apr 6 2024 to Apr 5 2025)
        tax_2024_start = date(2024, 4, 6)
        tax_2024_end = date(2025, 4, 5)

        income_tax_2024 = Income.objects.filter(
            user=user, date__gte=tax_2024_start, date__lte=tax_2024_end
        ).count()

        expense_tax_2024 = Expense.objects.filter(
            user=user, date__gte=tax_2024_start, date__lte=tax_2024_end
        ).count()

        if income_tax_2024 > 0 or expense_tax_2024 > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✓ YES - Found {income_tax_2024} income and {expense_tax_2024} expense records in tax year 2024-2025"
                )
            )

        self.stdout.write("\n" + "=" * 60 + "\n")
