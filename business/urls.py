# business/urls.py
from django.urls import path
from . import views

app_name = "business"

urlpatterns = [
    path("", views.business_list, name="business_list"),
    path("create/", views.business_create, name="business_create"),
    path("<int:pk>/", views.business_detail, name="business_detail"),
    path("<int:pk>/edit/", views.business_edit, name="business_edit"),
    path(
        "<int:pk>/delete/",
        views.business_confirm_delete,
        name="business_confirm_delete",
    ),
]
