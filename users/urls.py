from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserRegisterViewSet, UserProfileViewSet, UserHostelViewSet, MessProvidersViewSet, UnifiedSearchSuggestionAPIView

router = DefaultRouter()
router.register("register", UserRegisterViewSet, basename="user-register")
router.register("profile", UserProfileViewSet, basename="user-profile")
router.register("hostels", UserHostelViewSet, basename="hostel")
router.register("mess",MessProvidersViewSet, basename="mess")


urlpatterns = [
    path("", include(router.urls)),
    path("search/suggestions/", UnifiedSearchSuggestionAPIView.as_view(), name="search-suggestions"),
]
