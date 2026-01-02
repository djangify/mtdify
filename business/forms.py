# business/forms.py
from django import forms
from django.core.exceptions import ValidationError
from datetime import date

from .models import Business


class BusinessForm(forms.ModelForm):
    """Full business form with all fields."""

    class Meta:
        model = Business
        fields = [
            "name",
            "business_type",
            "trade_name",
            "accounting_period_start",
            "accounting_period_end",
            "cash_or_accruals",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "w-full border px-3 py-2 rounded"}),
            "business_type": forms.Select(
                attrs={"class": "w-full border px-3 py-2 rounded"}
            ),
            "trade_name": forms.TextInput(
                attrs={"class": "w-full border px-3 py-2 rounded"}
            ),
            "accounting_period_start": forms.DateInput(
                attrs={"type": "date", "class": "w-full border px-3 py-2 rounded"},
                format="%Y-%m-%d",
            ),
            "accounting_period_end": forms.DateInput(
                attrs={"type": "date", "class": "w-full border px-3 py-2 rounded"},
                format="%Y-%m-%d",
            ),
            "cash_or_accruals": forms.RadioSelect(),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if self.user:
            self.instance.user = self.user

        # Format dates as ISO so <input type="date"> accepts them
        for field_name in ["accounting_period_start", "accounting_period_end"]:
            value = getattr(self.instance, field_name, None)
            if value:
                self.fields[field_name].initial = value.strftime("%Y-%m-%d")

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("accounting_period_start")
        end = cleaned.get("accounting_period_end")

        if start and end:
            if end <= start:
                raise ValidationError(
                    {"accounting_period_end": "End date must be after the start date."}
                )

            delta = (end - start).days
            if delta < 300:
                raise ValidationError(
                    {
                        "accounting_period_end": "Accounting period appears too short (under 10 months)."
                    }
                )
            if delta > 545:
                raise ValidationError(
                    {
                        "accounting_period_end": "Accounting period appears too long (over 18 months)."
                    }
                )

        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        if self.user and not obj.user_id:
            obj.user = self.user
        if commit:
            obj.save()
        return obj


class BusinessQuickCreateForm(forms.ModelForm):
    """Simplified form with UK tax year defaults."""

    class Meta:
        model = Business
        fields = ["name", "business_type", "cash_or_accruals"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "w-full border px-3 py-2 rounded"}),
            "business_type": forms.Select(
                attrs={"class": "w-full border px-3 py-2 rounded"}
            ),
            "cash_or_accruals": forms.RadioSelect(),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if self.user:
            self.instance.user = self.user

        # Default to current UK tax year (6 April - 5 April)
        today = date.today()
        if today.month >= 4 and today.day >= 6:
            self.instance.accounting_period_start = date(today.year, 4, 6)
            self.instance.accounting_period_end = date(today.year + 1, 4, 5)
        else:
            self.instance.accounting_period_start = date(today.year - 1, 4, 6)
            self.instance.accounting_period_end = date(today.year, 4, 5)

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not obj.trade_name:
            obj.trade_name = obj.name
        if self.user and not obj.user_id:
            obj.user = self.user
        if commit:
            obj.save()
        return obj
