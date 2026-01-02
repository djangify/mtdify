from datetime import date
from bookkeeping.models import RecurringEntry, Income, Expense


def run_recurring_for_user(user):
    """
    Process recurring entries for a user, catching up on all missed entries
    from start_date to today.
    """
    today = date.today()

    entries = RecurringEntry.objects.filter(
        user=user,
        is_active=True,
    )

    results = []

    for entry in entries:
        # Skip if not started yet
        if today < entry.start_date:
            continue

        # Skip if already ended
        if entry.end_date and today > entry.end_date:
            continue

        # Initialize next_run if it's None (first time processing)
        if entry.next_run is None:
            entry.next_run = entry.start_date
            entry.save()

        # Calculate all due dates from next_run up to today
        due_dates = []
        current_due = entry.next_run

        # Catch up on all missed entries
        while current_due <= today:
            # Check if we've passed the end_date
            if entry.end_date and current_due > entry.end_date:
                break

            due_dates.append(current_due)

            # Calculate next occurrence (monthly on specified day)
            next_month = current_due.month + 1
            next_year = current_due.year

            if next_month > 12:
                next_month = 1
                next_year += 1

            # Handle day_of_month validation (use last day of month if day doesn't exist)
            try:
                current_due = date(next_year, next_month, entry.day_of_month)
            except ValueError:
                # Day doesn't exist in this month (e.g., Feb 30), use last day
                from calendar import monthrange

                last_day = monthrange(next_year, next_month)[1]
                current_due = date(next_year, next_month, last_day)

        # Create transactions for all due dates
        for due_date in due_dates:
            if entry.entry_type == "income":
                Income.objects.create(
                    user=user,
                    category=entry.category,
                    description=entry.description,
                    amount=entry.amount,
                    client_name=entry.client_name,
                    date=due_date,
                )
                results.append(f"Created income for {entry.description} on {due_date}")
            else:
                # Calculate VAT amount
                vat_amount = (
                    (entry.amount * entry.vat_rate / 100) if entry.vat_rate else 0
                )

                Expense.objects.create(
                    user=user,
                    category=entry.category,
                    description=entry.description,
                    amount=entry.amount,
                    vat_rate=entry.vat_rate,
                    vat_amount=vat_amount,
                    supplier_name=entry.supplier_name,
                    date=due_date,
                )
                results.append(f"Created expense for {entry.description} on {due_date}")

        # Update entry's tracking fields if we processed anything
        if due_dates:
            entry.last_run = due_dates[-1]  # Last processed date
            entry.next_run = current_due  # Next scheduled date
            entry.save()

    return results
