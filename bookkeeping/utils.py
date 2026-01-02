# bookkeeping/utils.py
"""
Tax year utilities for UK tax year management (6 April - 5 April)
"""

from datetime import date


def get_current_tax_year():
    """
    Get the current UK tax year.

    Returns:
        str: Current tax year in format "2024-2025"
    """
    today = date.today()
    return get_tax_year_from_date(today)


def get_tax_year_from_date(input_date):
    """
    Calculate UK tax year from a given date.
    """
    if input_date.month < 4 or (input_date.month == 4 and input_date.day < 6):
        return f"{input_date.year - 1}-{input_date.year}"
    else:
        return f"{input_date.year}-{input_date.year + 1}"


def get_tax_year_bounds(tax_year_string):
    """
    Given '2024-2025', return the start and end dates for that tax year.
    """
    start_year = int(tax_year_string.split("-")[0])
    end_year = int(tax_year_string.split("-")[1])

    return date(start_year, 4, 6), date(end_year, 4, 5)


def get_available_tax_years(user):
    """
    Get all tax years that contain data for this user.
    """
    from bookkeeping.models import Income, Expense

    all_income_dates = Income.objects.filter(user=user).values_list("date", flat=True)
    all_expense_dates = Expense.objects.filter(user=user).values_list("date", flat=True)

    all_dates = list(all_income_dates) + list(all_expense_dates)

    if not all_dates:
        return [get_current_tax_year()]

    tax_years = set()
    for d in all_dates:
        if d:
            tax_years.add(get_tax_year_from_date(d))

    if not tax_years:
        return [get_current_tax_year()]

    return sorted(list(tax_years), reverse=True)


def format_tax_year_display(tax_year_string):
    return f"Tax Year {tax_year_string}"


def get_tax_year_label(tax_year_string):
    if not tax_year_string:
        return ""
    start_year = tax_year_string.split("-")[0]
    end_year = tax_year_string.split("-")[1][-2:]
    return f"{start_year}/{end_year}"
