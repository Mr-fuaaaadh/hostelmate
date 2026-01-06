from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import RoomViewSet, FacilityViewSet, RoomImageViewSet

router = DefaultRouter()
router.register("rooms", RoomViewSet, basename="rooms")
router.register("facilities", FacilityViewSet, basename="facilities")
router.register("room-images", RoomImageViewSet, basename="room-images")

urlpatterns = [
    path("", include(router.urls)),
]
