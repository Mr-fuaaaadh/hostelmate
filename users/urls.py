from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserRegisterViewSet, UserProfileViewSet, UserHostelViewSet

router = DefaultRouter()
router.register("register", UserRegisterViewSet, basename="user-register")
router.register("profile", UserProfileViewSet, basename="user-profile")
router.register("hostels", UserHostelViewSet, basename="hostel")
# router.register("mess",MessProvidersViewSet, basename="mess")


urlpatterns = [
    path("", include(router.urls)),
]
