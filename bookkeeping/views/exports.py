from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from bookkeeping.models import Category, Income, Expense
import csv


# ----------------------------------------------------
# SCREEN: List all categories available for export
# ----------------------------------------------------
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
# EXPORT TRANSACTIONS FOR ONE CATEGORY
# ----------------------------------------------------
def export_category_csv(request, slug):
    category = get_object_or_404(Category, slug=slug)

    expenses = Expense.objects.filter(category=category)
    incomes = Income.objects.filter(category=category)

    response = HttpResponse(content_type="text/csv")
    filename = f"{category.slug}-export.csv"
    response["Content-Disposition"] = f"attachment; filename={filename}"

    writer = csv.writer(response)
    writer.writerow(["Type", "Date", "Description", "Amount", "Supplier/Client"])

    for item in incomes:
        writer.writerow(
            [
                "Income",
                item.date,
                item.description,
                item.amount,
                item.client_name or "",
            ]
        )

    for item in expenses:
        writer.writerow(
            [
                "Expense",
                item.date,
                item.description,
                item.amount,
                item.supplier_name or "",
            ]
        )

    return response


# ----------------------------------------------------
# EXPORT BY CATEGORY (OLD FORMAT)
# ----------------------------------------------------
def export_by_category(request, slug):
    category = Category.objects.get(slug=slug)

    expenses = Expense.objects.filter(category=category)
    income = Income.objects.filter(category=category)

    response = HttpResponse(content_type="text/csv")
    filename = f"{category.slug}-export.csv"
    response["Content-Disposition"] = f"attachment; filename={filename}"

    writer = csv.writer(response)
    writer.writerow(["Type", "Date", "Amount", "Supplier", "Client", "Description"])

    for item in income:
        writer.writerow(
            [
                "Income",
                item.date,
                item.amount,
                item.client_name,
                item.description,
            ]
        )

    for item in expenses:
        writer.writerow(
            [
                "Expense",
                item.date,
                item.amount,
                item.supplier_name,
                item.description,
            ]
        )

    return response
