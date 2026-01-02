# business/admin.py
from django.contrib import admin
from .models import Business


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    """Admin interface for Business model"""

    list_display = [
        "name",
        "user",
        "business_type",
        "accounting_period_start",
        "accounting_period_end",
        "cash_or_accruals",
        "created_at",
    ]

    list_filter = [
        "business_type",
        "cash_or_accruals",
        "created_at",
        "accounting_period_start",
    ]

    search_fields = [
        "name",
        "trade_name",
        "user__email",
        "user__first_name",
        "user__last_name",
    ]

    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Business Information",
            {"fields": ("user", "name", "trade_name", "business_type")},
        ),
        (
            "Accounting Details",
            {
                "fields": (
                    "accounting_period_start",
                    "accounting_period_end",
                    "cash_or_accruals",
                )
            },
        ),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    autocomplete_fields = ["user"]
    ordering = ["-created_at"]
