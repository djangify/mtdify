from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from datetime import datetime
import csv
from bookkeeping.utils import get_current_tax_year, get_tax_year_bounds
from bookkeeping.models import Income, Expense


def get_quarter_summary(user, quarter_code):
    """
    Get financial summary for a specific quarter.
    Returns: dict with income, expenses, vat, profit
    """
    income_total = (
        Income.objects.filter(user=user, quarter=quarter_code).aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    expense_aggregates = Expense.objects.filter(
        user=user, quarter=quarter_code
    ).aggregate(total_net=Sum("amount"), total_vat=Sum("vat_amount"))

    expense_total = expense_aggregates["total_net"] or 0
    vat_total = expense_aggregates["total_vat"] or 0
    profit = income_total - expense_total

    return {
        "income": income_total,
        "expenses": expense_total,
        "vat": vat_total,
        "profit": profit,
    }


# ---------------------------------------------
# YEARLY PROFIT REPORT — CSV EXPORT
# ---------------------------------------------
@login_required
def yearly_profit_report_csv(request):
    """
    Generate a comprehensive yearly profit report CSV with:
    - Tax year summary
    - Quarterly breakdown
    - YTD totals
    - Income by category
    - Expenses by category
    """
    user = request.user
    # Get selected tax year from session
    selected_tax_year = request.session.get("selected_tax_year")

    if not selected_tax_year:
        selected_tax_year = get_current_tax_year()

    tax_year_start, tax_year_end = get_tax_year_bounds(selected_tax_year)
    tax_year_label = selected_tax_year

    # Prepare CSV response
    response = HttpResponse(content_type="text/csv")
    filename = f"yearly_profit_report_{tax_year_label.replace('-', '_')}.csv"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)

    # =========================================
    # SECTION 1: TAX YEAR SUMMARY
    # =========================================
    writer.writerow(["YEARLY PROFIT REPORT"])
    writer.writerow(["MTDify Local Edition"])
    writer.writerow(["Generated:", datetime.now().strftime("%d/%m/%Y %H:%M")])
    writer.writerow([])

    writer.writerow(["TAX YEAR SUMMARY"])
    writer.writerow(["Tax Year:", tax_year_label])
    writer.writerow(
        [
            "Period:",
            f"{tax_year_start.strftime('%d/%m/%Y')} - {tax_year_end.strftime('%d/%m/%Y')}",
        ]
    )
    writer.writerow([])

    # =========================================
    # SECTION 2: QUARTERLY BREAKDOWN
    # =========================================
    writer.writerow(["QUARTERLY BREAKDOWN"])
    writer.writerow(
        ["Quarter", "Income (£)", "Expenses (£)", "VAT (£)", "Net Profit (£)"]
    )

    # Extract year from tax_year_label (e.g., "2024-2025" -> 2024)
    year = int(tax_year_label.split("-")[0])

    quarters = [f"{year}-Q1", f"{year}-Q2", f"{year}-Q3", f"{year}-Q4"]
    quarterly_totals = {
        "income": 0,
        "expenses": 0,
        "vat": 0,
        "profit": 0,
    }

    for quarter in quarters:
        summary = get_quarter_summary(user, quarter)
        writer.writerow(
            [
                quarter,
                f"{summary['income']:.2f}",
                f"{summary['expenses']:.2f}",
                f"{summary['vat']:.2f}",
                f"{summary['profit']:.2f}",
            ]
        )

        # Accumulate totals
        quarterly_totals["income"] += summary["income"]
        quarterly_totals["expenses"] += summary["expenses"]
        quarterly_totals["vat"] += summary["vat"]
        quarterly_totals["profit"] += summary["profit"]

    # Quarterly totals row
    writer.writerow(
        [
            "TOTAL",
            f"{quarterly_totals['income']:.2f}",
            f"{quarterly_totals['expenses']:.2f}",
            f"{quarterly_totals['vat']:.2f}",
            f"{quarterly_totals['profit']:.2f}",
        ]
    )
    writer.writerow([])

    # =========================================
    # SECTION 3: YEAR-TO-DATE TOTALS
    # =========================================
    ytd_income = (
        Income.objects.filter(user=user, date__gte=tax_year_start).aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    ytd_aggregates = Expense.objects.filter(
        user=user, date__gte=tax_year_start
    ).aggregate(total_net=Sum("amount"), total_vat=Sum("vat_amount"))

    ytd_expenses = ytd_aggregates["total_net"] or 0
    ytd_vat = ytd_aggregates["total_vat"] or 0
    ytd_profit = ytd_income - ytd_expenses

    writer.writerow(["YEAR-TO-DATE TOTALS"])
    writer.writerow(["Description", "Amount (£)"])
    writer.writerow(["Total Income", f"{ytd_income:.2f}"])
    writer.writerow(["Total Expenses", f"{ytd_expenses:.2f}"])
    writer.writerow(["Total VAT", f"{ytd_vat:.2f}"])
    writer.writerow(["Net Profit", f"{ytd_profit:.2f}"])
    writer.writerow([])

    # =========================================
    # SECTION 4: INCOME BY CATEGORY
    # =========================================
    income_categories = (
        Income.objects.filter(user=user, date__gte=tax_year_start)
        .values("category__name")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("category__name")
    )

    writer.writerow(["INCOME BY CATEGORY"])
    writer.writerow(["Category", "Total (£)", "Number of Entries", "Average (£)"])

    for cat in income_categories:
        average = cat["total"] / cat["count"] if cat["count"] > 0 else 0
        writer.writerow(
            [
                cat["category__name"],
                f"{cat['total']:.2f}",
                cat["count"],
                f"{average:.2f}",
            ]
        )

    # Income category total
    income_cat_total = sum(cat["total"] for cat in income_categories)
    income_cat_count = sum(cat["count"] for cat in income_categories)
    writer.writerow(
        [
            "TOTAL",
            f"{income_cat_total:.2f}",
            income_cat_count,
            "",
        ]
    )
    writer.writerow([])

    # =========================================
    # SECTION 5: EXPENSES BY CATEGORY
    # =========================================
    expense_categories = (
        Expense.objects.filter(user=user, date__gte=tax_year_start)
        .values("category__name")
        .annotate(
            total_net=Sum("amount"), total_vat=Sum("vat_amount"), count=Count("id")
        )
        .order_by("category__name")
    )

    writer.writerow(["EXPENSES BY CATEGORY"])
    writer.writerow(
        [
            "Category",
            "Net Amount (£)",
            "VAT (£)",
            "Total Inc VAT (£)",
            "Number of Entries",
            "Average (£)",
        ]
    )

    for cat in expense_categories:
        total_inc_vat = cat["total_net"] + cat["total_vat"]
        average = cat["total_net"] / cat["count"] if cat["count"] > 0 else 0
        writer.writerow(
            [
                cat["category__name"],
                f"{cat['total_net']:.2f}",
                f"{cat['total_vat']:.2f}",
                f"{total_inc_vat:.2f}",
                cat["count"],
                f"{average:.2f}",
            ]
        )

    # Expense category totals
    expense_cat_net = sum(cat["total_net"] for cat in expense_categories)
    expense_cat_vat = sum(cat["total_vat"] for cat in expense_categories)
    expense_cat_total_inc = expense_cat_net + expense_cat_vat
    expense_cat_count = sum(cat["count"] for cat in expense_categories)
    writer.writerow(
        [
            "TOTAL",
            f"{expense_cat_net:.2f}",
            f"{expense_cat_vat:.2f}",
            f"{expense_cat_total_inc:.2f}",
            expense_cat_count,
            "",
        ]
    )
    writer.writerow([])

    # =========================================
    # SECTION 6: REPORT FOOTER
    # =========================================
    writer.writerow(["REPORT SUMMARY"])
    writer.writerow(["Total Transactions:", income_cat_count + expense_cat_count])
    writer.writerow(["Income Entries:", income_cat_count])
    writer.writerow(["Expense Entries:", expense_cat_count])
    writer.writerow([])
    writer.writerow(["Report generated by MTDify Local Edition"])
    writer.writerow(["https://mtdify.uk"])

    return response


# ---------------------------------------------
# INCOME BY CATEGORY — CSV EXPORT
# ---------------------------------------------
@login_required
def income_category_csv(request):
    user = request.user
    # Get selected tax year from session
    selected_tax_year = request.session.get("selected_tax_year")

    if not selected_tax_year:
        selected_tax_year = get_current_tax_year()

    tax_year_start, tax_year_end = get_tax_year_bounds(selected_tax_year)

    rows = (
        Income.objects.filter(
            user=user, date__gte=tax_year_start, date__lte=tax_year_end
        )
        .values("category__name")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("category__name")
    )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="income_by_category.csv"'

    writer = csv.writer(response)
    writer.writerow(["Category", "Total Amount", "Number of Entries"])

    for row in rows:
        writer.writerow(
            [
                row["category__name"],
                f"{row['total']:.2f}",
                row["count"],
            ]
        )

    return response


# ---------------------------------------------
# INCOME BY CATEGORY — PRINT VIEW
# ---------------------------------------------
@login_required
def income_category_print(request):
    user = request.user

    rows = (
        Income.objects.filter(user=user)
        .values("category__name")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("category__name")
    )

    total_income = rows.aggregate(Sum("total"))["total__sum"] or 0

    return render(
        request,
        "bookkeeping/reports/income_category_print.html",
        {
            "categories": rows,
            "total_income": total_income,
            "today": datetime.now(),
        },
    )


# ---------------------------------------------
# COMBINED CATEGORY TOTALS — CSV EXPORT
# ---------------------------------------------
@login_required
def combined_category_csv(request):
    user = request.user
    # Get selected tax year from session
    selected_tax_year = request.session.get("selected_tax_year")

    if not selected_tax_year:
        selected_tax_year = get_current_tax_year()

    tax_year_start, tax_year_end = get_tax_year_bounds(selected_tax_year)

    income_rows = (
        Income.objects.filter(
            user=user, date__gte=tax_year_start, date__lte=tax_year_end
        )
        .values("category__name")
        .annotate(total=Sum("amount"))
    )

    expense_rows = (
        Expense.objects.filter(
            user=user, date__gte=tax_year_start, date__lte=tax_year_end
        )
        .values("category__name")
        .annotate(total=Sum("amount"))
    )

    income_map = {i["category__name"]: i["total"] for i in income_rows}
    expense_map = {e["category__name"]: e["total"] for e in expense_rows}

    all_cats = sorted(set(income_map.keys()) | set(expense_map.keys()))

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        'attachment; filename="combined_category_totals.csv"'
    )

    writer = csv.writer(response)
    writer.writerow(["Category", "Income", "Expenses", "Net"])

    for cat in all_cats:
        inc = income_map.get(cat, 0)
        exp = expense_map.get(cat, 0)
        writer.writerow([cat, f"{inc:.2f}", f"{exp:.2f}", f"{(inc - exp):.2f}"])

    return response


# ---------------------------------------------
# COMBINED CATEGORY TOTALS — PRINT VIEW
# ---------------------------------------------
@login_required
def combined_category_print(request):
    user = request.user
    # Get selected tax year from session
    selected_tax_year = request.session.get("selected_tax_year")

    if not selected_tax_year:
        selected_tax_year = get_current_tax_year()

    tax_year_start, tax_year_end = get_tax_year_bounds(selected_tax_year)

    income_rows = (
        Income.objects.filter(user=user)
        .values("category__name")
        .annotate(total=Sum("amount"))
        .order_by("category__name")
    )

    expense_rows = (
        Expense.objects.filter(user=user)
        .values("category__name")
        .annotate(total=Sum("amount"))
        .order_by("category__name")
    )

    income_map = {i["category__name"]: i["total"] for i in income_rows}
    expense_map = {e["category__name"]: e["total"] for e in expense_rows}

    all_cats = sorted(set(income_map.keys()) | set(expense_map.keys()))

    rows = []
    for cat in all_cats:
        inc = income_map.get(cat, 0)
        exp = expense_map.get(cat, 0)
        rows.append(
            {
                "category": cat,
                "income": inc,
                "expenses": exp,
                "net": inc - exp,
            }
        )

    return render(
        request,
        "bookkeeping/reports/combined_category_print.html",
        {
            "rows": rows,
            "today": datetime.now(),
        },
    )
