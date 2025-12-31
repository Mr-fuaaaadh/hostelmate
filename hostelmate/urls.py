from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# ---------------------------------------------------------------------
# Main URL Configuration
# ---------------------------------------------------------------------
urlpatterns = [
    # Admin Panel
    path("admin/", admin.site.urls),

    # JWT Authentication (SimpleJWT)
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Application Routes
    path("api/users/", include("users.urls")),
    path("api/hostels/", include("hostels.urls")),
    path("api/rooms/", include("rooms.urls")),
]

# ---------------------------------------------------------------------
# Static & Media Files (Development Only)
# ---------------------------------------------------------------------
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
