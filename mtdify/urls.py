from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
]
# ---- STATIC/MEDIA ----
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Adminita - Admin customization
admin.site.site_header = "Bookkeeping Software"
admin.site.site_title = "Bookkeeping Software"
admin.site.index_title = "Welcome to Your Site"
