from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import HttpResponse
import csv

from bookkeeping.models import Expense, Category
from bookkeeping.forms import ExpenseForm


# ===========================
# EXPENSE LIST
# ===========================
@login_required
def expense_list(request):
    from bookkeeping.utils import get_tax_year_bounds

    # Get selected tax year from session
    selected_tax_year = request.session.get("selected_tax_year")

    # Base queryset
    qs = Expense.objects.filter(user=request.user).select_related("category")

    # ⚠️ FIX: Only filter by tax year if one is selected AND it's not "all"
    if selected_tax_year and selected_tax_year != "all":
        tax_year_start, tax_year_end = get_tax_year_bounds(selected_tax_year)
        qs = qs.filter(date__gte=tax_year_start, date__lte=tax_year_end)

    # Search
    search = request.GET.get("search")
    if search:
        qs = qs.filter(
            Q(description__icontains=search) | Q(supplier_name__icontains=search)
        )

    # Quarter
    quarter = request.GET.get("quarter")
    if quarter:
        qs = qs.filter(quarter=quarter)

    # Category
    category_id = request.GET.get("category")
    if category_id:
        qs = qs.filter(category_id=category_id)

    # Date range
    date_from = request.GET.get("date_from")
    if date_from:
        qs = qs.filter(date__gte=date_from)

    date_to = request.GET.get("date_to")
    if date_to:
        qs = qs.filter(date__lte=date_to)

    # Receipt filter
    receipt_filter = request.GET.get("has_receipt")
    if receipt_filter == "yes":
        qs = qs.exclude(receipt="")
    elif receipt_filter == "no":
        qs = qs.filter(receipt="")

    # Ordering
    order_by = request.GET.get("order_by", "-date")
    qs = qs.order_by(order_by)

    # Totals
    totals = qs.aggregate(total=Sum("amount"), total_vat=Sum("vat_amount"))
    total_expenses = totals["total"] or 0
    total_vat = totals["total_vat"] or 0

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get("page"))

    # ⚠️ FIX: Get quarters from the FILTERED queryset
    quarters = qs.values_list("quarter", flat=True).distinct().order_by("-quarter")

    return render(
        request,
        "bookkeeping/expense/expense_list.html",
        {
            "expense_list": page,
            "total_expenses": total_expenses,
            "total_vat": total_vat,
            "expense_categories": Category.objects.filter(category_type="expense"),
            "quarters": quarters,
            # ⚠️ FIX: Pass selected_tax_year to template
            "selected_tax_year": selected_tax_year,
            # Filter persistence
            "search_query": search,
            "filter_date_from": date_from,
            "filter_date_to": date_to,
            "filter_category": category_id,
            "filter_quarter": quarter,
            "filter_has_receipt": receipt_filter,
            "order_by": order_by,
        },
    )


# ===========================
# CREATE EXPENSE
# ===========================
@login_required
def expense_create(request):
    if request.method == "POST":
        form = ExpenseForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()

            if "save_and_add" in request.POST:
                return redirect("bookkeeping:expense_create")
            return redirect("bookkeeping:expense_list")
    else:
        form = ExpenseForm(user=request.user)

    return render(
        request,
        "bookkeeping/expense/expense_form.html",
        {"form": form},
    )


# ===========================
# EXPENSE DETAIL
# ===========================
@login_required
def expense_detail(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    total = expense.amount + expense.vat_amount
    return render(
        request,
        "bookkeeping/expense/expense_detail.html",
        {"expense": expense, "total": total},
    )


# ===========================
# EDIT EXPENSE
# ===========================
@login_required
def expense_edit(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)

    if request.method == "POST":
        form = ExpenseForm(
            request.POST, request.FILES, instance=expense, user=request.user
        )
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            return redirect("bookkeeping:expense_detail", pk=expense.pk)
    else:
        form = ExpenseForm(instance=expense, user=request.user)

    return render(
        request,
        "bookkeeping/expense/expense_edit.html",
        {"form": form, "expense": expense},
    )


# ===========================
# DELETE EXPENSE
# ===========================
@login_required
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)

    if request.method == "POST":
        # Delete receipt file if it exists
        if expense.receipt:
            expense.receipt.delete()
        expense.delete()
        messages.success(request, "Expense entry deleted.")
        return redirect("bookkeeping:expense_list")

    return render(
        request,
        "bookkeeping/expense/expense_confirm_delete.html",
        {"expense": expense},
    )


# ===========================
# EXPORT EXPENSE CSV
# ===========================
@login_required
def export_expense_csv(request):
    from bookkeeping.utils import get_tax_year_bounds

    # Get selected tax year
    selected_tax_year = request.session.get("selected_tax_year", "all")

    # Base queryset
    expenses = Expense.objects.filter(user=request.user)

    # Filter by tax year if selected and not "all"
    if selected_tax_year and selected_tax_year != "all":
        tax_year_start, tax_year_end = get_tax_year_bounds(selected_tax_year)
        expenses = expenses.filter(date__gte=tax_year_start, date__lte=tax_year_end)

    expenses = expenses.order_by("-date")

    # Create filename with tax year
    year_suffix = (
        selected_tax_year.replace("-", "_") if selected_tax_year != "all" else "all"
    )
    filename = f"expenses_{year_suffix}.csv"

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(["Date", "Description", "Supplier", "Amount", "VAT", "Category"])

    for item in expenses:
        writer.writerow(
            [
                item.date,
                item.description,
                item.supplier_name or "",
                item.amount,
                item.vat_amount,
                item.category.name if item.category else "",
            ]
        )

    return response
