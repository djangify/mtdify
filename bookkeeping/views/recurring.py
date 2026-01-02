from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator

from bookkeeping.models import RecurringEntry, Category
from bookkeeping.forms import RecurringEntryForm
from bookkeeping.services import run_recurring_for_user


# ----------------------------------------
# LIST RECURRING ENTRIES
# ----------------------------------------
@login_required
def recurring_list(request):
    qs = RecurringEntry.objects.filter(user=request.user).select_related("category")

    # Optional filters
    entry_type = request.GET.get("entry_type")
    if entry_type:
        qs = qs.filter(entry_type=entry_type)

    category_id = request.GET.get("category")
    if category_id:
        qs = qs.filter(category_id=category_id)

    is_active = request.GET.get("active")
    if is_active == "yes":
        qs = qs.filter(is_active=True)
    elif is_active == "no":
        qs = qs.filter(is_active=False)

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "bookkeeping/recurring/recurring_list.html",
        {
            "recurring_list": page,
            "filter_entry_type": entry_type,
            "filter_category": category_id,
            "filter_active": is_active,
            "categories": Category.objects.all(),
        },
    )


# ----------------------------------------
# CREATE RECURRING ENTRY
# ----------------------------------------
@login_required
def recurring_create(request):
    """List recurring entries with filtering & pagination."""
    if request.method == "POST":
        form = RecurringEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.save()

            # Catch up on missed entries immediately
            run_recurring_for_user(request.user)

            messages.success(request, "Recurring entry created.")
            return redirect("bookkeeping:recurring_list")
    else:
        form = RecurringEntryForm()

    return render(
        request,
        "bookkeeping/recurring/recurring_form.html",
        {"form": form},
    )


# ----------------------------------------
# EDIT RECURRING ENTRY
# ----------------------------------------
@login_required
def recurring_edit(request, pk):
    """List recurring entries with filtering & pagination."""
    entry = get_object_or_404(RecurringEntry, pk=pk, user=request.user)

    if request.method == "POST":
        form = RecurringEntryForm(request.POST, instance=entry)
        if form.is_valid():
            updated = form.save(commit=False)
            updated.user = request.user
            updated.save()

            # Recalculate if start date or billing schedule changed
            run_recurring_for_user(request.user)

            messages.success(request, "Recurring entry updated.")
            return redirect("bookkeeping:recurring_list")
    else:
        form = RecurringEntryForm(instance=entry)

    return render(
        request,
        "bookkeeping/recurring/recurring_edit.html",
        {"form": form},
    )


# ----------------------------------------
# DELETE RECURRING ENTRY
# ----------------------------------------
@login_required
def recurring_delete(request, pk):
    entry = get_object_or_404(RecurringEntry, pk=pk, user=request.user)

    if request.method == "POST":
        entry.delete()
        messages.success(request, "Recurring entry deleted.")
        return redirect("bookkeeping:recurring_list")

    return render(
        request,
        "bookkeeping/recurring/recurring_confirm_delete.html",
        {"entry": entry},
    )
