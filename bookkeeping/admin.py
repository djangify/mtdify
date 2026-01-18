# bookkeeping/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.db import models
from django.template.response import TemplateResponse
from django.urls import path

from .models import Category, Income, Expense, ProfitAndLoss, RecurringRunLog

# ===========================
# CATEGORY ADMIN
# ===========================


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "category_type", "is_active", "created_at", "slug"]
    list_filter = ["category_type", "is_active", "created_at"]
    search_fields = ["name", "slug"]

    # slug + created_at must be read-only
    readonly_fields = ["slug", "created_at"]

    fieldsets = (
        ("Category Information", {"fields": ("name", "category_type", "slug")}),
        ("Status", {"fields": ("is_active",)}),
        (
            "Metadata",
            {
                "fields": ("created_at",),
                "classes": ("collapse",),
            },
        ),
    )

    ordering = ["category_type", "name"]


# ===========================
# INCOME ADMIN
# ===========================


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = [
        "formatted_date",
        "user",
        "description",
        "amount_display",
        "category",
        "quarter",
        "created_at",
    ]

    list_filter = ["quarter", "category", "date", "created_at"]
    search_fields = ["description", "client_name", "invoice_number", "user__email"]
    readonly_fields = ["quarter", "created_at", "updated_at"]
    ordering = ["-date"]
    autocomplete_fields = ["user"]
    date_hierarchy = "date"

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("user", "date", "description", "amount", "category")},
        ),
        (
            "Client Details",
            {"fields": ("client_name", "invoice_number"), "classes": ("collapse",)},
        ),
        ("Quarter Info", {"fields": ("quarter",)}),
        ("Notes", {"fields": ("notes",), "classes": ("collapse",)}),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    # Display helpers
    def formatted_date(self, obj):
        return obj.date.strftime("%d/%m/%Y") if obj.date else "—"

    formatted_date.short_description = "Date"
    formatted_date.admin_order_field = "date"

    def amount_display(self, obj):
        try:
            return format_html("<strong>£{:,.2f}</strong>", float(obj.amount or 0))
        except Exception:
            return "—"

    amount_display.short_description = "Amount"

    # Custom summary in change list
    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)
        if hasattr(response, "context_data"):
            qs = response.context_data["cl"].queryset
            total = qs.aggregate(total=models.Sum("amount"))["total"] or 0
            response.context_data["summary"] = {"total": f"£{total:,.2f}"}
        return response


# ===========================
# EXPENSE ADMIN
# ===========================


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = [
        "formatted_date",
        "user",
        "description",
        "amount_display",
        "vat_display",
        "category",
        "quarter",
        "has_receipt",
        "created_at",
    ]

    list_filter = ["quarter", "category", "date", "created_at"]
    search_fields = ["description", "supplier_name", "user__email"]
    readonly_fields = ["quarter", "created_at", "updated_at", "receipt_preview"]
    ordering = ["-date"]
    autocomplete_fields = ["user"]
    date_hierarchy = "date"

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("user", "date", "description", "amount", "category")},
        ),
        (
            "VAT Details",
            {"fields": ("vat_amount", "vat_rate"), "classes": ("collapse",)},
        ),
        ("Supplier", {"fields": ("supplier_name",), "classes": ("collapse",)}),
        ("Receipt", {"fields": ("receipt", "receipt_preview")}),
        ("Quarter Info", {"fields": ("quarter",)}),
        ("Notes", {"fields": ("notes",), "classes": ("collapse",)}),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def formatted_date(self, obj):
        return obj.date.strftime("%d/%m/%Y") if obj.date else "—"

    formatted_date.short_description = "Date"

    def amount_display(self, obj):
        try:
            return format_html("<strong>£{:,.2f}</strong>", float(obj.amount or 0))
        except Exception:
            return "—"

    amount_display.short_description = "Amount"

    def vat_display(self, obj):
        if obj.vat_amount:
            return (
                f"£{obj.vat_amount:.2f} ({obj.vat_rate}%)"
                if obj.vat_rate
                else f"£{obj.vat_amount:.2f}"
            )
        return "—"

    vat_display.short_description = "VAT"

    def has_receipt(self, obj):
        return "✓" if obj.receipt else "✗"

    has_receipt.short_description = "Receipt"

    def receipt_preview(self, obj):
        if obj.receipt:
            url = obj.receipt.url
            if url.lower().endswith(".pdf"):
                return format_html(
                    '<a href="{}" target="_blank" style="display:inline-block;padding:10px 15px;background:#e5e7eb;border-radius:4px;">📄 View PDF Receipt</a>',
                    url,
                )
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="max-width: 200px;" /></a>',
                url,
                url,
            )
        return "No receipt"

    receipt_preview.short_description = "Preview"

    # Custom summary
    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)
        if hasattr(response, "context_data"):
            qs = response.context_data["cl"].queryset
            total = qs.aggregate(total=models.Sum("amount"))["total"] or 0
            vat_total = qs.aggregate(v=models.Sum("vat_amount"))["v"] or 0
            response.context_data["summary"] = {
                "total": f"£{total:,.2f}",
                "vat_total": f"£{vat_total:,.2f}",
            }
        return response


# ===========================
# PROFIT & LOSS (virtual model)
# ===========================


class ProfitAndLossAdmin(admin.ModelAdmin):
    change_list_template = "admin/bookkeeping/summary.html"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "",
                self.admin_site.admin_view(self.summary_view),
                name="bookkeeping_profit_summary",
            )
        ]
        return custom + urls

    def summary_view(self, request):
        income_total = (
            Income.objects.aggregate(total=models.Sum("amount"))["total"] or 0
        )
        expense_total = (
            Expense.objects.aggregate(total=models.Sum("amount"))["total"] or 0
        )
        profit = income_total - expense_total

        context = dict(
            self.admin_site.each_context(request),
            title="Profit & Loss Summary",
            income_total=f"£{income_total:,.2f}",
            expense_total=f"£{expense_total:,.2f}",
            profit=f"£{profit:,.2f}",
        )
        return TemplateResponse(request, "admin/bookkeeping/summary.html", context)


admin.site.register(ProfitAndLoss, ProfitAndLossAdmin)


# ===========================
# RECURRING ENTRY CHECKS
# ===========================
@admin.register(RecurringRunLog)
class RecurringRunLogAdmin(admin.ModelAdmin):
    list_display = ["user", "last_run_date"]
    readonly_fields = ["last_run_date"]
