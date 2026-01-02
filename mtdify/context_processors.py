# mtdify/context_processors.py
"""
Context processors for MTDify templates.
"""

from django.conf import settings
from bookkeeping.utils import (
    get_available_tax_years,
    get_tax_year_label,
)


def version(request):
    """Add version number to all templates."""
    return {"MTDIFY_VERSION": settings.MTDIFY_VERSION}


def tax_year_data(request):
    """
    Add tax year context to all templates.
    Makes selected_tax_year, available_tax_years, and tax_year_short
    available in every template.
    """
    context = {}

    # Check user is authenticated and has a valid id
    if hasattr(request, "user") and request.user.is_authenticated and request.user.id:
        try:
            selected_year = request.session.get("selected_tax_year", "")
            available_years = get_available_tax_years(request.user)

            context = {
                "selected_tax_year": selected_year,
                "available_tax_years": available_years,
                "tax_year_short": get_tax_year_label(selected_year)
                if selected_year
                else "",
            }

        except Exception as e:
            # If anything fails, return empty context
            print(f"Error in tax_year_data context processor: {e}")

    return context
