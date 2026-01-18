from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.core.exceptions import ValidationError
from datetime import datetime
from datetime import date
from django.utils.text import slugify

User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=255)
    category_type = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(blank=True, null=True)

    def save(self, *args, **kwargs):
        base_slug = slugify(self.name)

        if not self.slug:
            slug = base_slug
            counter = 1

            while Category.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Income(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="incomes")
    date = models.DateField(db_index=True)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
    )

    client_name = models.CharField(max_length=200, blank=True)
    invoice_number = models.CharField(max_length=100, blank=True)

    quarter = models.CharField(max_length=10, db_index=True, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date"]

    def save(self, *args, **kwargs):
        self.quarter = self._calculate_quarter()
        super().save(*args, **kwargs)

    def _calculate_quarter(self):
        date = self.date
        if isinstance(date, str):
            date = datetime.strptime(date, "%Y-%m-%d").date()

        # Tax year handling
        if date.month > 4 or (date.month == 4 and date.day >= 6):
            year = date.year
        else:
            year = date.year - 1

        # Quarter breakpoints
        if (
            (date.month == 4 and date.day >= 6)
            or date.month in [5, 6]
            or (date.month == 7 and date.day <= 5)
        ):
            return f"{year}-Q1"
        elif (
            (date.month == 7 and date.day >= 6)
            or date.month in [8, 9]
            or (date.month == 10 and date.day <= 5)
        ):
            return f"{year}-Q2"
        elif (
            (date.month == 10 and date.day >= 6)
            or date.month in [11, 12]
            or (date.month == 1 and date.day <= 5)
        ):
            return f"{year}-Q3"
        else:
            return f"{year}-Q4"


class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="expenses")
    date = models.DateField(db_index=True)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        limit_choices_to={"category_type": "expense"},
    )

    vat_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    vat_rate = models.DecimalField(
        max_digits=4, decimal_places=2, default=Decimal("0.00")
    )

    supplier_name = models.CharField(max_length=200, blank=True)
    receipt = models.FileField(upload_to="receipts/%Y/%m/", blank=True, null=True)

    quarter = models.CharField(max_length=10, db_index=True, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date"]

    def save(self, *args, **kwargs):
        self.quarter = self._calculate_quarter()
        super().save(*args, **kwargs)

    def clean(self):
        if self.vat_rate and self.vat_rate > 0:
            expected_vat = round(float(self.amount) * float(self.vat_rate) / 100, 2)
            actual_vat = round(float(self.vat_amount or 0), 2)
            if abs(expected_vat - actual_vat) > 0.05:
                raise ValidationError(
                    {
                        "vat_amount": (
                            f"VAT amount £{actual_vat:.2f} does not match "
                            f"{self.vat_rate:.0f}% of £{self.amount:.2f} "
                            f"(should be £{expected_vat:.2f})."
                        )
                    }
                )

    def _calculate_quarter(self):
        return Income._calculate_quarter(self)


class ProfitAndLoss(models.Model):
    class Meta:
        managed = False
        verbose_name_plural = "Profit & Loss Summary"

    def __str__(self):
        return "Profit & Loss Summary"


class RecurringEntry(models.Model):
    ENTRY_TYPE_CHOICES = [
        ("income", "Income"),
        ("expense", "Expense"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="recurring_entries"
    )

    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPE_CHOICES)

    # Category limits match existing Income/Expense logic
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
    )

    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Expense-only metadata (safe to keep optional)
    vat_rate = models.DecimalField(
        max_digits=4, decimal_places=2, default=Decimal("0.00"), blank=True
    )
    supplier_name = models.CharField(max_length=200, blank=True)

    # Income-only metadata (optional)
    client_name = models.CharField(max_length=200, blank=True)

    # Recurrence fields
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)

    # Monthly only (for now)
    day_of_month = models.PositiveIntegerField(default=1)

    last_run = models.DateField(null=True, blank=True)
    next_run = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["day_of_month", "entry_type"]
        verbose_name = "Recurring Entry"
        verbose_name_plural = "Recurring Entries"

    def __str__(self):
        return f"{self.entry_type.capitalize()} – {self.description} (£{self.amount})"

    def clean(self):
        """Model-level validation"""
        super().clean()
        if self.day_of_month < 1 or self.day_of_month > 28:
            raise ValidationError(
                {
                    "day_of_month": "Day must be between 1 and 28 to avoid month-end issues."
                }
            )

    def save(self, *args, **kwargs):
        # Initialize next_run on creation
        if self.next_run is None:
            self.next_run = self.start_date
        super().save(*args, **kwargs)

    def calculate_next_run(self):
        # First time: use start_date
        if self.last_run is None:
            return self.start_date

        year = self.last_run.year
        month = self.last_run.month + 1

        if month > 12:
            month = 1
            year += 1

        # Day of month already validated (1–28)
        return date(year, month, self.day_of_month)


class RecurringRunLog(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    last_run_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Recurring run log for {self.user.email}"

    class Meta:
        verbose_name = "Recurring Run Log"
        verbose_name_plural = "Recurring Run Logs"
