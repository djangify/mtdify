# business/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Business
from .forms import BusinessForm, BusinessQuickCreateForm


@login_required
def business_list(request):
    """List all businesses for the logged-in user."""
    qs = Business.objects.filter(user=request.user)

    # Filter by business type
    business_type = request.GET.get("business_type")
    if business_type:
        qs = qs.filter(business_type=business_type)

    # Filter by accounting basis
    basis = request.GET.get("cash_or_accruals")
    if basis:
        qs = qs.filter(cash_or_accruals=basis)

    # Search
    search = request.GET.get("search")
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(trade_name__icontains=search))

    # Ordering
    order_by = request.GET.get("order_by", "-created_at")
    qs = qs.order_by(order_by)

    paginator = Paginator(qs, 10)
    page = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "business/business_list.html",
        {
            "business_list": page,
            "business_count": qs.count(),
            "business_types": Business.BUSINESS_TYPE_CHOICES,
            "filter_business_type": business_type,
            "filter_cash_or_accruals": basis,
            "search_query": search,
            "order_by": order_by,
        },
    )


@login_required
def business_create(request):
    """Create a new business. Limited to one business per user."""
    # Block creation if user already has a business
    if Business.objects.filter(user=request.user).exists():
        messages.error(request, "You can only have one business.")
        return redirect("business:business_list")

    if request.method == "POST":
        form = BusinessForm(request.POST, user=request.user)
        if form.is_valid():
            business = form.save(commit=False)
            business.user = request.user
            business.save()
            messages.success(request, "Your business has been created.")
            return redirect("business:business_detail", pk=business.pk)
    else:
        form = BusinessForm(user=request.user)

    return render(request, "business/business_form.html", {"form": form})


@login_required
def business_detail(request, pk):
    """View business details."""
    business = get_object_or_404(Business, pk=pk, user=request.user)
    return render(request, "business/business_detail.html", {"business": business})


@login_required
def business_edit(request, pk):
    """Edit an existing business."""
    business = get_object_or_404(Business, pk=pk, user=request.user)

    if request.method == "POST":
        form = BusinessForm(request.POST, instance=business, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Business updated.")
            return redirect("business:business_detail", pk=pk)
    else:
        form = BusinessForm(instance=business, user=request.user)

    return render(
        request,
        "business/business_edit.html",
        {"form": form, "business": business},
    )


@login_required
def business_quick_create(request):
    """Quick create with UK tax year defaults."""
    if request.method == "POST":
        form = BusinessQuickCreateForm(request.POST, user=request.user)
        if form.is_valid():
            business = form.save()
            messages.success(request, f"Business '{business.name}' created.")
            return redirect("business:business_detail", pk=business.pk)
    else:
        form = BusinessQuickCreateForm(user=request.user)

    return render(
        request,
        "business/business_form.html",
        {"form": form, "is_quick_form": True},
    )


@login_required
def business_confirm_delete(request, pk):
    """Confirm and delete a business."""
    business = get_object_or_404(Business, pk=pk, user=request.user)

    if request.method == "POST":
        name = business.name
        business.delete()
        messages.success(request, f"Business '{name}' deleted.")
        return redirect("business:business_list")

    return render(
        request,
        "business/business_confirm_delete.html",
        {"business": business},
    )
