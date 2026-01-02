# business/models.py
from django.db import models
from django.conf import settings


class Business(models.Model):
    """
    Represents a business the user tracks.
    One user = one business (for sole traders).
    """

    BUSINESS_TYPE_CHOICES = [
        ("self-employment", "Self Employment"),
        ("uk-property", "UK Property"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="business",
    )
    name = models.CharField(max_length=200)
    business_type = models.CharField(max_length=20, choices=BUSINESS_TYPE_CHOICES)
    trade_name = models.CharField(max_length=200, blank=True)

    accounting_period_start = models.DateField()
    accounting_period_end = models.DateField()

    cash_or_accruals = models.CharField(
        max_length=10,
        choices=[("cash", "Cash"), ("accruals", "Accruals")],
        default="cash",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Businesses"

    def __str__(self):
        return f"{self.name} ({self.get_business_type_display()})"
