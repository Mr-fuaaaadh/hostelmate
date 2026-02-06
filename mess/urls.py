from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserHomeViewSet, HomeImageViewSet, MessMenuViewSet

router = DefaultRouter()
router.register(r"homes", UserHomeViewSet, basename="homes")
router.register(r"home-images", HomeImageViewSet, basename="home-images")
router.register(r'mess-menu', MessMenuViewSet, basename='mess-menu')



urlpatterns = [
    path("", include(router.urls)),
]
