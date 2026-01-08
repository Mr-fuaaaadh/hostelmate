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
    queryset = Facility.objects.filter(is_active=True)
    serializer_class = FacilitySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]




class RoomViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
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
        """
        Optimized production-standard queryset.
        - select_related: One SQL hit for hostel and its owner.
        - prefetch_related: Separate optimized queries for images and facilities.
        """
        return Room.objects.filter(
            hostel__owner=self.request.user
        ).select_related("hostel__owner").prefetch_related(
            "images", 
            "room_facilities__facility"
        )

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update", "create"]:
            return RoomWriteSerializer
        return RoomReadSerializer

    def perform_create(self, serializer):
        # Additional safety check: Ensure the user owns the hostel they are adding a room to
        hostel = serializer.validated_data.get('hostel')
        if hostel.owner != self.request.user:
            raise ValidationError({"hostel": "You do not have permission to add rooms to this hostel."})
        
        room = serializer.save()
        import logging
        logger = logging.getLogger(__name__)
        print(f"Room {room.id} created for hostel {room.hostel.id} by user {self.request.user.id}")


class RoomImageViewSet(viewsets.ModelViewSet):
    serializer_class = RoomImageSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["room"]

    def get_queryset(self):
        return RoomImage.objects.filter(
            room__hostel__owner=self.request.user
        )

    def perform_create(self, serializer):
        room = serializer.validated_data.get("room")
        print(room)

        if not room:
            raise ValidationError({"room": "Room is required"})

        if room.hostel.owner != self.request.user:
            raise ValidationError({"room": "This room does not belong to you"})

        serializer.save()



