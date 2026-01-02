# bookkeeping/urls.py
from django.urls import path
from bookkeeping.views import (
    income,
    expense,
    recurring,
    exports,
    reports,
)

app_name = "bookkeeping"

urlpatterns = [
    # ------------------------------
    # INCOME
    # ------------------------------
    path("income/", income.income_list, name="income_list"),
    path("income/add/", income.income_create, name="income_create"),
    path("income/<int:pk>/", income.income_detail, name="income_detail"),
    path("income/<int:pk>/edit/", income.income_edit, name="income_edit"),
    path("income/<int:pk>/delete/", income.income_delete, name="income_confirm_delete"),
    path("income/export/csv/", income.export_income_csv, name="income_export_csv"),
    # ------------------------------
    # EXPENSE
    # ------------------------------
    path("expense/", expense.expense_list, name="expense_list"),
    path("expense/add/", expense.expense_create, name="expense_create"),
    path("expense/<int:pk>/", expense.expense_detail, name="expense_detail"),
    path("expense/<int:pk>/edit/", expense.expense_edit, name="expense_edit"),
    path(
        "expense/<int:pk>/delete/",
        expense.expense_delete,
        name="expense_confirm_delete",
    ),
    path("expense/export/csv/", expense.export_expense_csv, name="expense_export_csv"),
    # ------------------------------
    # RECURRING
    # ------------------------------
    path("recurring/", recurring.recurring_list, name="recurring_list"),
    path("recurring/add/", recurring.recurring_create, name="recurring_create"),
    path("recurring/<int:pk>/edit/", recurring.recurring_edit, name="recurring_edit"),
    path(
        "recurring/<int:pk>/delete/",
        recurring.recurring_delete,
        name="recurring_delete",
    ),
    # ------------------------------
    # CATEGORY EXPORTS (Legacy + New)
    # ------------------------------
    path(
        "export/category/<slug:slug>/",
        exports.export_by_category,
        name="export_by_category",
    ),
    path(
        "export/categories/",
        exports.export_categories_screen,
        name="export_categories_screen",
    ),
    path(
        "export/categories/<slug:slug>/",
        exports.export_category_csv,
        name="export_category_csv",
    ),
    # ------------------------------
    # CATEGORY TOTAL REPORTS
    # ------------------------------
    path(
        "reports/income-category/csv/",
        reports.income_category_csv,
        name="income_category_csv",
    ),
    path(
        "reports/income-category/print/",
        reports.income_category_print,
        name="income_category_print",
    ),
    path(
        "reports/combined-category/csv/",
        reports.combined_category_csv,
        name="combined_category_csv",
    ),
    path(
        "reports/combined-category/print/",
        reports.combined_category_print,
        name="combined_category_print",
    ),
    # ------------------------------
    # NEW: YEARLY PROFIT REPORT
    # ------------------------------
    path(
        "reports/yearly-profit-csv/",
        reports.yearly_profit_report_csv,
        name="yearly_profit_csv",
    ),
]
