from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from bookkeeping.models import Income, Category
from bookkeeping.forms import IncomeForm
import csv
from django.http import HttpResponse


# ===========================
# INCOME LIST
# ===========================
@login_required
def income_list(request):
    from bookkeeping.utils import get_tax_year_bounds

    # Get selected tax year from session
    selected_tax_year = request.session.get("selected_tax_year")

    # Base queryset
    qs = Income.objects.filter(user=request.user).select_related("category")

    # ⚠️ FIX: Only filter by tax year if one is selected AND it's not "all"
    if selected_tax_year and selected_tax_year != "all":
        tax_year_start, tax_year_end = get_tax_year_bounds(selected_tax_year)
        qs = qs.filter(date__gte=tax_year_start, date__lte=tax_year_end)

    # Additional filters
    search = request.GET.get("search")
    if search:
        qs = qs.filter(
            Q(description__icontains=search)
            | Q(client_name__icontains=search)
            | Q(invoice_number__icontains=search)
        )

    quarter = request.GET.get("quarter")
    if quarter:
        qs = qs.filter(quarter=quarter)

    category_id = request.GET.get("category")
    if category_id:
        qs = qs.filter(category_id=category_id)

    date_from = request.GET.get("date_from")
    if date_from:
        qs = qs.filter(date__gte=date_from)

    date_to = request.GET.get("date_to")
    if date_to:
        qs = qs.filter(date__lte=date_to)

    order_by = request.GET.get("order_by", "-date")
    qs = qs.order_by(order_by)

    total_income = qs.aggregate(total=Sum("amount"))["total"] or 0

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get("page"))

    # ⚠️ FIX: Get quarters from the FILTERED queryset, not all user income
    quarters = qs.values_list("quarter", flat=True).distinct().order_by("-quarter")

    context = {
        "income_list": page,
        "total_income": total_income,
        "income_categories": Category.objects.filter(category_type="income"),
        "quarters": quarters,
        # ⚠️ FIX: Pass selected_tax_year to template
        "selected_tax_year": selected_tax_year,
        # Filter values for form persistence
        "search_query": search,
        "filter_date_from": date_from,
        "filter_date_to": date_to,
        "filter_category": category_id,
        "filter_quarter": quarter,
        "order_by": order_by,
    }

    return render(request, "bookkeeping/income/income_list.html", context)


# ===========================
# CREATE INCOME
# ===========================
@login_required
def income_create(request):
    if request.method == "POST":
        form = IncomeForm(request.POST, user=request.user)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()

            if "save_and_add" in request.POST:
                return redirect("bookkeeping:income_create")
            return redirect("bookkeeping:income_list")
    else:
        form = IncomeForm(user=request.user)

    return render(request, "bookkeeping/income/income_form.html", {"form": form})


# ===========================
# INCOME DETAIL
# ===========================
@login_required
def income_detail(request, pk):
    income = get_object_or_404(Income, pk=pk, user=request.user)
    return render(request, "bookkeeping/income/income_detail.html", {"income": income})


# ===========================
# EDIT INCOME
# ===========================
@login_required
def income_edit(request, pk):
    income = get_object_or_404(Income, pk=pk, user=request.user)

    if request.method == "POST":
        form = IncomeForm(request.POST, instance=income, user=request.user)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            return redirect("bookkeeping:income_detail", pk=income.pk)
    else:
        form = IncomeForm(instance=income, user=request.user)

    return render(
        request, "bookkeeping/income/income_edit.html", {"form": form, "income": income}
    )


# ===========================
# DELETE INCOME
# ===========================
@login_required
def income_delete(request, pk):
    income = get_object_or_404(Income, pk=pk, user=request.user)

    if request.method == "POST":
        income.delete()
        messages.success(request, "Income entry deleted.")
        return redirect("bookkeeping:income_list")

    return render(
        request, "bookkeeping/income/income_confirm_delete.html", {"income": income}
    )


# ===========================
# EXPORT INCOME CSV
# ===========================
@login_required
def export_income_csv(request):
    from bookkeeping.utils import get_tax_year_bounds

    # Get selected tax year
    selected_tax_year = request.session.get("selected_tax_year", "all")

    # Base queryset
    incomes = Income.objects.filter(user=request.user)

    # Filter by tax year if selected and not "all"
    if selected_tax_year and selected_tax_year != "all":
        tax_year_start, tax_year_end = get_tax_year_bounds(selected_tax_year)
        incomes = incomes.filter(date__gte=tax_year_start, date__lte=tax_year_end)

    incomes = incomes.order_by("-date")

    # Create filename with tax year
    year_suffix = (
        selected_tax_year.replace("-", "_") if selected_tax_year != "all" else "all"
    )
    filename = f"income_{year_suffix}.csv"

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(
        ["Date", "Description", "Client", "Net Amount", "VAT Amount", "Category"]
    )

    for item in incomes:
        writer.writerow(
            [
                item.date,
                item.description,
                item.client_name or "",
                item.amount,
                item.vat_amount if hasattr(item, "vat_amount") else 0,
                item.category.name if item.category else "",
            ]
        )

    return response
