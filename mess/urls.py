from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserHomeViewSet

router = DefaultRouter()
router.register(r"homes", UserHomeViewSet, basename="homes")

urlpatterns = [
    path("", include(router.urls)),
]
