from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import RoomViewSet, FacilityViewSet

router = DefaultRouter()
router.register(r'rooms', RoomViewSet, basename='room')
router.register(r'facilities', FacilityViewSet, basename='facility')

urlpatterns = [
    path('', include(router.urls)),
]
