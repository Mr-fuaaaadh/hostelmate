from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import Room, Facility, RoomImage, RoomFacility
from .serializers import (
    RoomSerializer,
    RoomCreateUpdateSerializer,
    FacilitySerializer,
    RoomImageSerializer,
    RoomFacilitySerializer,
)
from hostels.permissions import IsOwnerOrReadOnly, IsAdminOrReadOnly

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class FacilityViewSet(viewsets.ModelViewSet):
    queryset = Facility.objects.filter(is_active=True)
    serializer_class = FacilitySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]




class RoomViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    pagination_class = StandardResultsSetPagination
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = ["hostel", "room_type", "is_available"]
    search_fields = ["room_number", "hostel__name"]
    ordering_fields = ["daily_price", "monthly_price", "capacity"]
    ordering = ["room_number"]

    def get_queryset(self):
        return Room.objects.filter(
            hostel__owner=self.request.user
        ).select_related("hostel").prefetch_related(
            "images", "room_facilities__facility"
        )

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return RoomCreateUpdateSerializer
        return RoomSerializer


class RoomImageViewSet(viewsets.ModelViewSet):
    serializer_class = RoomImageSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    pagination_class = StandardResultsSetPagination
    parser_classes = [MultiPartParser, FormParser]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["room"]
    search_fields = ["room__room_number"]

    def get_queryset(self):
        return RoomImage.objects.filter(
            room__hostel__owner=self.request.user
        ).select_related("room", "room__hostel")
