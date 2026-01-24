from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.exceptions import ValidationError
from .models import Room, Facility, RoomImage, RoomFacility
from .serializers import (
    RoomReadSerializer,
    RoomWriteSerializer,
    FacilitySerializer,
    RoomImageSerializer
)
from hostels.permissions import IsOwnerOrReadOnly, IsAdminOrReadOnly

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class FacilityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing room facilities.
    Provides standard CRUD operations with search capabilities.
    """
    queryset = Facility.objects.filter(is_active=True)
    serializer_class = FacilitySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]


class RoomViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing hostel rooms.
    Supports filtering, searching, and optimized data retrieval.
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    parser_classes = [MultiPartParser, FormParser, JSONParser]

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
        """
        Retrieves optimized queryset of rooms owned by the current user.
        Uses select_related and prefetch_related to minimize database hits.
        """
        return Room.objects.filter(
            hostel__owner=self.request.user
        ).select_related("hostel").prefetch_related(
            "images", 
            "room_facilities__facility"
        )

    def get_serializer_class(self):
        """
        Returns different serializers for read and write operations.
        """
        if self.action in ["create", "update", "partial_update"]:
            return RoomWriteSerializer
        return RoomReadSerializer

    def perform_create(self, serializer):
        """
        Ensures the hostel associated with the new room is owned by the user.
        """
        hostel = serializer.validated_data.get('hostel')
        if hostel and hostel.owner != self.request.user:
            raise ValidationError(
                {"hostel": "You do not have permission to add rooms to this hostel."}
            )
        
        serializer.save()


class RoomImageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing room images.
    Restricted to images of rooms owned by the current user.
    """
    serializer_class = RoomImageSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["room"]

    def get_queryset(self):
        """
        Limits visibility to images of rooms owned by the authorized user.
        """
        return RoomImage.objects.filter(
            room__hostel__owner=self.request.user
        ).select_related("room__hostel")

    def perform_create(self, serializer):
        """
        Validates ownership of the room before allowing image upload.
        """
        room = serializer.validated_data.get("room")
        if not room:
            raise ValidationError({"room": "Room is required"})

        if room.hostel.owner != self.request.user:
            raise ValidationError({"room": "This room does not belong to you"})

        serializer.save()



