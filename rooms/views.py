from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from .models import Room, Facility, RoomImage, RoomFacility
from .serializers import RoomSerializer, RoomCreateUpdateSerializer, FacilitySerializer, RoomImageSerializer, RoomFacilitySerializer
from hostels.permissions import IsOwnerOrReadOnly, IsAdminOrReadOnly

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50

class FacilityViewSet(viewsets.ModelViewSet):
    queryset = Facility.objects.filter(is_active=True)
    serializer_class = FacilitySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.select_related('hostel').prefetch_related('images', 'room_facilities__facility')
    permission_classes = [IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['hostel', 'room_type', 'is_available']
    search_fields = ['room_number', 'hostel__name']
    ordering_fields = ['daily_price', 'monthly_price', 'capacity']
    ordering = ['room_number']
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RoomCreateUpdateSerializer
        return RoomSerializer

    @action(detail=True, methods=['post'])
    def add_images(self, request, pk=None):
        room = self.get_object()
        images = request.FILES.getlist('images')
        for image in images:
            RoomImage.objects.create(room=room, image=image)
        return Response({'status': 'Images added'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def add_facilities(self, request, pk=None):
        room = self.get_object()
        facilities = request.data.get("facilities", [])
        for facility_id in facilities:
            RoomFacility.objects.get_or_create(room=room, facility_id=facility_id)
        return Response({"status": "Facilities added"}, status=status.HTTP_200_OK)
