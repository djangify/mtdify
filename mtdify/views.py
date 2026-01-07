from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils.timezone import now
from bookkeeping.models import Income, Expense
from bookkeeping.services import run_recurring_for_user
from django.contrib.auth import logout
from bookkeeping.models import RecurringRunLog
from django.contrib import messages
from django.http import JsonResponse


def home(request):
    return render(request, "home.html")


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def switch_tax_year(request, tax_year):
    """
    Switch the active tax year for the user's session.
    """
    from bookkeeping.utils import get_available_tax_years

    # Validate that this tax year is available
    available_years = get_available_tax_years(request.user)

    if tax_year in available_years:
        request.session["selected_tax_year"] = tax_year
        messages.success(request, f"Switched to Tax Year {tax_year}")
    else:
        messages.error(request, f"Tax year {tax_year} not available")

    # Redirect back to referring page or dashboard
    return redirect(request.META.get("HTTP_REFERER", "dashboard"))


@login_required
def dashboard(request):
    """
    Dashboard view for MTDify Local Edition.
    Shows totals for the selected tax year + quarter figures + recent items.
    """
    from bookkeeping.utils import get_tax_year_bounds, get_current_tax_year

    user = request.user
    today = now().date()

    # Get selected tax year from session
    selected_tax_year = request.session.get("selected_tax_year")

    if not selected_tax_year:
        selected_tax_year = get_current_tax_year()
        request.session["selected_tax_year"] = selected_tax_year

    # Get tax year boundaries
    tax_year_start, tax_year_end = get_tax_year_bounds(selected_tax_year)

    # --- DAILY LOCK FOR RECURRING TASKS ---
    log, created = RecurringRunLog.objects.get_or_create(user=user)

    if log.last_run_date != today:
        run_recurring_for_user(user)
        log.last_run_date = today
        log.save()

    # -------------------------------
    # YTD totals (for selected tax year)
    # -------------------------------
    ytd_income = (
        Income.objects.filter(
            user=user, date__gte=tax_year_start, date__lte=tax_year_end
        )
        .aggregate(total=Sum("amount"))
        .get("total")
        or 0
    )

    ytd_expenses = (
        Expense.objects.filter(
            user=user, date__gte=tax_year_start, date__lte=tax_year_end
        )
        .aggregate(total=Sum("amount"))
        .get("total")
        or 0
    )

    ytd_profit = ytd_income - ytd_expenses

    # -------------------------------
    # Determine current quarter (only if viewing current tax year)
    # -------------------------------
    if selected_tax_year == get_current_tax_year():
        # Show current quarter data
        latest_q_income = (
            Income.objects.filter(user=user)
            .order_by("-date")
            .values_list("quarter", flat=True)
            .first()
        )
        latest_q_expense = (
            Expense.objects.filter(user=user)
            .order_by("-date")
            .values_list("quarter", flat=True)
            .first()
        )

        current_quarter = latest_q_income or latest_q_expense or "N/A"
    else:
        # For historical years, show Q4 as the "last quarter"
        year = int(selected_tax_year.split("-")[0])
        current_quarter = f"{year}-Q4"

    # -------------------------------
    # Quarter totals
    # -------------------------------
    quarter_income = (
        Income.objects.filter(user=user, quarter=current_quarter)
        .aggregate(total=Sum("amount"))
        .get("total")
        or 0
    )

    quarter_expenses = (
        Expense.objects.filter(user=user, quarter=current_quarter)
        .aggregate(total=Sum("amount"))
        .get("total")
        or 0
    )

    quarter_profit = quarter_income - quarter_expenses

    # -------------------------------
    # Recent items (from selected tax year only)
    # -------------------------------
    recent_income = Income.objects.filter(
        user=user, date__gte=tax_year_start, date__lte=tax_year_end
    ).order_by("-date")[:5]

    recent_expenses = Expense.objects.filter(
        user=user, date__gte=tax_year_start, date__lte=tax_year_end
    ).order_by("-date")[:5]

    # -------------------------------
    # Send everything to template
    # -------------------------------
    context = {
        # Selected tax year
        "selected_tax_year": selected_tax_year,
        "tax_year": selected_tax_year,
        # Quarter
        "current_quarter": current_quarter,
        "quarter_income": quarter_income,
        "quarter_expenses": quarter_expenses,
        "quarter_profit": quarter_profit,
        # Year-to-date
        "ytd_income": ytd_income,
        "ytd_expenses": ytd_expenses,
        "ytd_profit": ytd_profit,
        # Existing fields
        "total_income": ytd_income,
        "total_expenses": ytd_expenses,
        "business_count": 1,
        "recent_income": recent_income,
        "recent_expenses": recent_expenses,
    }

    return render(request, "dashboard.html", context)


def health_check(request):
    """Health check endpoint for Docker/container monitoring."""
    return JsonResponse({"status": "healthy"}, status=200)
