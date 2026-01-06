# bookkeeping/views/exports.py

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from datetime import datetime
import csv

from bookkeeping.models import Category, Income, Expense
from bookkeeping.utils import get_current_tax_year, get_tax_year_bounds


# ----------------------------------------------------
# SCREEN: List all categories available for export
# ----------------------------------------------------
@login_required
def export_categories_screen(request):
    categories = Category.objects.filter(is_active=True).order_by(
        "category_type", "name"
    )
    return render(
        request,
        "bookkeeping/export_categories.html",
        {"categories": categories},
    )


# ----------------------------------------------------
# EXPORT TRANSACTIONS FOR ONE CATEGORY (CSV)
# ----------------------------------------------------
@login_required
def export_category_csv(request, slug):
    user = request.user

    # Get selected tax year from session
    selected_tax_year = request.session.get("selected_tax_year")
    if not selected_tax_year:
        selected_tax_year = get_current_tax_year()
    tax_year_start, tax_year_end = get_tax_year_bounds(selected_tax_year)

    # Handle special "all-expenses" case
    if slug == "all-expenses":
        expenses = (
            Expense.objects.filter(
                user=user, date__gte=tax_year_start, date__lte=tax_year_end
            )
            .select_related("category")
            .order_by("-date")
        )
        incomes = Income.objects.none()
        filename = f"all-expenses-{selected_tax_year}.csv"
        category_name = "All Expenses"
    else:
        category = get_object_or_404(Category, slug=slug)
        category_name = category.name

        expenses = Expense.objects.filter(
            user=user,
            category=category,
            date__gte=tax_year_start,
            date__lte=tax_year_end,
        ).order_by("-date")

        incomes = Income.objects.filter(
            user=user,
            category=category,
            date__gte=tax_year_start,
            date__lte=tax_year_end,
        ).order_by("-date")

        filename = f"{category.slug}-{selected_tax_year}.csv"

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(
        ["Type", "Date", "Description", "Amount", "Category", "Supplier/Client"]
    )

    for item in incomes:
        writer.writerow(
            [
                "Income",
                item.date.strftime("%d/%m/%Y"),
                item.description,
                f"{item.amount:.2f}",
                item.category.name if item.category else "",
                item.client_name or "",
            ]
        )

    for item in expenses:
        writer.writerow(
            [
                "Expense",
                item.date.strftime("%d/%m/%Y"),
                item.description,
                f"{item.amount:.2f}",
                item.category.name if item.category else "",
                item.supplier_name or "",
            ]
        )

    return response


# ----------------------------------------------------
# EXPORT BY CATEGORY (PRINT VIEW)
# ----------------------------------------------------
@login_required
def export_by_category(request, slug):
    user = request.user

    # Get selected tax year from session
    selected_tax_year = request.session.get("selected_tax_year")
    if not selected_tax_year:
        selected_tax_year = get_current_tax_year()
    tax_year_start, tax_year_end = get_tax_year_bounds(selected_tax_year)

    # Handle special "all-expenses" case
    if slug == "all-expenses":
        expenses = (
            Expense.objects.filter(
                user=user, date__gte=tax_year_start, date__lte=tax_year_end
            )
            .select_related("category")
            .order_by("category__name", "-date")
        )
        category_name = "All Expenses"
    else:
        category = get_object_or_404(Category, slug=slug)
        expenses = (
            Expense.objects.filter(
                user=user,
                category=category,
                date__gte=tax_year_start,
                date__lte=tax_year_end,
            )
            .select_related("category")
            .order_by("-date")
        )
        category_name = category.name

    # Calculate totals
    total_amount = expenses.aggregate(total=Sum("amount"))["total"] or 0
    total_vat = expenses.aggregate(total=Sum("vat_amount"))["total"] or 0

    # Group expenses by category for the "all-expenses" view
    expenses_by_category = {}
    if slug == "all-expenses":
        for expense in expenses:
            cat_name = expense.category.name if expense.category else "Uncategorised"
            if cat_name not in expenses_by_category:
                expenses_by_category[cat_name] = {
                    "items": [],
                    "total": 0,
                    "vat_total": 0,
                }
            expenses_by_category[cat_name]["items"].append(expense)
            expenses_by_category[cat_name]["total"] += expense.amount
            expenses_by_category[cat_name]["vat_total"] += expense.vat_amount or 0

    return render(
        request,
        "bookkeeping/reports/expenses_by_category_print.html",
        {
            "expenses": expenses,
            "expenses_by_category": expenses_by_category,
            "category_name": category_name,
            "is_all_expenses": slug == "all-expenses",
            "total_amount": total_amount,
            "total_vat": total_vat,
            "tax_year": selected_tax_year,
            "today": datetime.now(),
        },
    )
