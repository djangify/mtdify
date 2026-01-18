# bookkeeping/forms.py

from django import forms
from .models import Income, Expense, Category, RecurringEntry
from decimal import Decimal
from secure_uploads.forms import SecureUploadMixin


# ============================================================
# CATEGORY FORM
# ============================================================


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "category_type", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "w-full border px-3 py-2 rounded"}),
            "category_type": forms.Select(
                attrs={"class": "w-full border px-3 py-2 rounded"}
            ),
            "description": forms.Textarea(
                attrs={"class": "w-full border px-3 py-2 rounded", "rows": 3}
            ),
        }


# ============================================================
# INCOME FORM
# ============================================================


class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = [
            "date",
            "description",
            "amount",
            "category",
            "client_name",
            "invoice_number",
            "notes",
        ]
        widgets = {
            "date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full border px-3 py-2 rounded",
                },
                format="%Y-%m-%d",
            ),
            "description": forms.TextInput(
                attrs={
                    "class": "w-full border px-3 py-2 rounded",
                    "placeholder": "Brief description of the income",
                }
            ),
            "amount": forms.NumberInput(
                attrs={"step": "0.01", "class": "w-full border px-3 py-2 rounded"}
            ),
            "category": forms.Select(
                attrs={"class": "w-full border px-3 py-2 rounded"}
            ),
            "client_name": forms.TextInput(
                attrs={
                    "class": "w-full border px-3 py-2 rounded",
                    "placeholder": "Person or business who paid you",
                }
            ),
            "invoice_number": forms.TextInput(
                attrs={
                    "class": "w-full border px-3 py-2 rounded",
                    "placeholder": "Optional invoice reference",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "w-full border px-3 py-2 rounded",
                    "placeholder": "Additional notes (optional)",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Filter categories for income
        self.fields["category"].queryset = Category.objects.filter(
            category_type="income"
        )

        # Existing date automatically handled by Django — no overrides needed

    def save(self, commit=True):
        obj = super().save(commit=False)
        if self.user and not obj.user_id:
            obj.user = self.user
        if commit:
            obj.save()
        return obj

    def clean_day_of_month(self):
        """Validate day_of_month is between 1-28 to avoid month-end issues"""
        day = self.cleaned_data.get("day_of_month")

        if day is None:
            return day

        if day < 1 or day > 28:
            raise forms.ValidationError(
                "Day must be between 1 and 28 to avoid month-end issues."
            )

        return day


# ============================================================
# EXPENSE FORM
# ============================================================


class ExpenseForm(SecureUploadMixin, forms.ModelForm):
    image_fields = ["receipt"]

    class Meta:
        model = Expense
        fields = [
            "date",
            "description",
            "amount",
            "category",
            "supplier_name",
            "vat_rate",
            "vat_amount",
            "receipt",
            "notes",
        ]
        widgets = {
            "date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full border px-3 py-2 rounded",
                },
                format="%Y-%m-%d",
            ),
            "description": forms.TextInput(
                attrs={
                    "class": "w-full border px-3 py-2 rounded",
                    "placeholder": "Brief description of the expense",
                }
            ),
            "amount": forms.NumberInput(
                attrs={"step": "0.01", "class": "w-full border px-3 py-2 rounded"}
            ),
            "category": forms.Select(
                attrs={"class": "w-full border px-3 py-2 rounded"}
            ),
            "supplier_name": forms.TextInput(
                attrs={
                    "class": "w-full border px-3 py-2 rounded",
                    "placeholder": "Name of supplier (optional)",
                }
            ),
            "vat_rate": forms.NumberInput(
                attrs={"step": "0.01", "class": "w-full border px-3 py-2 rounded"}
            ),
            "vat_amount": forms.NumberInput(
                attrs={"step": "0.01", "class": "w-full border px-3 py-2 rounded"}
            ),
            "receipt": forms.FileInput(
                attrs={"class": "w-full border px-3 py-2 rounded"}
            ),
            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "w-full border px-3 py-2 rounded",
                    "placeholder": "Additional notes (optional)",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Filter categories for expenses
        self.fields["category"].queryset = Category.objects.filter(
            category_type="expense"
        )
        # Existing date automatically handled by Django — no overrides needed

    def clean(self):
        cleaned = super().clean()
        amount = cleaned.get("amount")
        vat_rate = cleaned.get("vat_rate")
        vat_amount = cleaned.get("vat_amount")

        # Only validate when all required fields are present and vat_rate > 0
        if (
            all([amount is not None, vat_rate is not None, vat_amount is not None])
            and vat_rate > 0
        ):
            # Calculate expected VAT using Decimal for precision
            expected_vat = (amount * vat_rate / Decimal("100")).quantize(
                Decimal("0.01")
            )
            actual_vat = vat_amount.quantize(Decimal("0.01"))

            # Calculate the difference
            difference = abs(expected_vat - actual_vat)

            if difference > Decimal("0.05"):
                # Large difference - show error
                self.add_error(
                    "vat_amount",
                    f"VAT amount £{actual_vat:.2f} does not match "
                    f"{vat_rate:.0f}% of £{amount:.2f} "
                    f"(should be £{expected_vat:.2f}).",
                )
            elif difference > Decimal("0.00"):
                # Small rounding difference (1p-5p) - auto-correct silently
                cleaned["vat_amount"] = expected_vat

        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        if self.user and not obj.user_id:
            obj.user = self.user
        if commit:
            obj.save()
        return obj


# ============================================================
# RECURRING ENTRY FORM
# ============================================================


class RecurringEntryForm(forms.ModelForm):
    class Meta:
        model = RecurringEntry
        fields = [
            "entry_type",
            "category",
            "description",
            "amount",
            "vat_rate",
            "supplier_name",
            "client_name",
            "start_date",
            "end_date",
            "day_of_month",
            "is_active",
        ]
        widgets = {
            "start_date": forms.DateInput(
                attrs={"type": "date", "class": "w-full border px-3 py-2 rounded"},
                format="%Y-%m-%d",
            ),
            "end_date": forms.DateInput(
                attrs={"type": "date", "class": "w-full border px-3 py-2 rounded"},
                format="%Y-%m-%d",
            ),
            "description": forms.TextInput(attrs={"placeholder": "Description"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 💡 CRITICAL: Ensure initial values are ISO formatted so the browser accepts them
        for field_name in ["start_date", "end_date"]:
            value = getattr(self.instance, field_name, None)
            if value:
                self.fields[field_name].initial = value.strftime("%Y-%m-%d")

        # Ensure input formats match HTML5 requirements
        self.fields["start_date"].input_formats = ["%Y-%m-%d"]
        self.fields["end_date"].input_formats = ["%Y-%m-%d"]

        # ENTRY TYPE SELECT
        self.fields["entry_type"].choices = [
            ("", "— Select Entry Type —"),
            ("income", "Income"),
            ("expense", "Expense"),
        ]
        self.fields["entry_type"].widget.attrs.update(
            {"class": "w-full border px-3 py-2 rounded"}
        )
        # CATEGORY SELECT (initially empty)
        self.fields["category"].queryset = Category.objects.none()
        self.fields["category"].widget.attrs.update(
            {"class": "w-full border px-3 py-2 rounded"}
        )

        # Determine entry_type from form POST or instance
        entry_type = None
        form_data = args[0] if args else None

        if isinstance(form_data, dict):
            entry_type = form_data.get("entry_type")

        if not entry_type and self.instance.pk:
            entry_type = self.instance.entry_type

        entry_type = (entry_type or "").lower()

        # Apply category filtering
        if entry_type == "income":
            self.fields["category"].queryset = Category.objects.filter(
                category_type="income", is_active=True
            )
        elif entry_type == "expense":
            self.fields["category"].queryset = Category.objects.filter(
                category_type="expense", is_active=True
            )

        # Optional fields
        self.fields["supplier_name"].required = False
        self.fields["client_name"].required = False
        self.fields["vat_rate"].required = False

    # -----------------------------
    # VALIDATION: Start < End date
    # -----------------------------
    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")

        if start and end and end < start:
            raise forms.ValidationError("End date cannot be before the start date.")

        return cleaned

    # -----------------------------
    # VALIDATION: Day of month 1–28
    # -----------------------------
    def clean_day_of_month(self):
        day = self.cleaned_data.get("day_of_month")

        if day is None:
            return day

        if day < 1 or day > 28:
            raise forms.ValidationError(
                "Day must be between 1 and 28 to avoid month-end issues."
            )

        return day

    # -----------------------------
    # SAVE
    # -----------------------------
    def save(self, commit=True):
        obj = super().save(commit=False)
        if commit:
            obj.save()
        return obj
