# mtdify/middleware.py
"""
Middleware for managing tax year selection across the application.
"""

from bookkeeping.utils import get_current_tax_year


class TaxYearMiddleware:
    """
    Middleware to ensure every request has a selected tax year in session.
    Defaults to current tax year if not set.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Ensure selected_tax_year exists in session
        if "selected_tax_year" not in request.session:
            request.session["selected_tax_year"] = get_current_tax_year()

        response = self.get_response(request)
        return response
