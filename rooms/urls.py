from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import RoomViewSet, FacilityViewSet, RoomImageViewSet

router = DefaultRouter()
router.register(r'rooms', RoomViewSet, basename='room')
router.register(r'facilities', FacilityViewSet, basename='facility')
router.register(r"room-images", RoomImageViewSet, basename="roomimage")
urlpatterns = [
    path('', include(router.urls)),
]
