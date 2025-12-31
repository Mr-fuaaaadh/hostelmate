from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from .models import Hostel, HostelFacility, HostelImage, HostelRule
from .serializers import HostelSerializer, HostelCreateUpdateSerializer, HostelImageSerializer, HostelRuleSerializer, HostelFacilitySerializer
from .permissions import IsOwnerOrReadOnly
import logging

logger = logging.getLogger(__name__)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class HostelViewSet(viewsets.ModelViewSet):
    """
    Only allows owners to view/edit their hostels.
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["city", "state", "is_verified", "hostel_type"]
    search_fields = ["name", "address", "city", "state"]
    ordering_fields = ["id", "created_at", "name"]
    ordering = ["-created_at"]

    def get_queryset(self):
        # Only return hostels owned by the logged-in user
        queryset = Hostel.objects.filter(owner=self.request.user)\
            .select_related("owner")\
            .prefetch_related(
                "hostel_facilities__facility", 
                "images", 
                "rules"
            )
        
        # Log hostel details for debugging
        logger.info(f"User {self.request.user} accessed hostels: {[h.id for h in queryset]}")
        return queryset

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return HostelCreateUpdateSerializer
        return HostelSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    # Custom actions
    @action(detail=True, methods=['post'])
    def add_facilities(self, request, pk=None):
        hostel = self.get_object()
        facilities = request.data.get("facilities", [])
        for facility_id in facilities:
            HostelFacility.objects.get_or_create(hostel=hostel, facility_id=facility_id)
        return Response({"status": "Facilities added"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def add_images(self, request, pk=None):
        hostel = self.get_object()
        images = request.FILES.getlist("images")
        for image in images:
            HostelImage.objects.create(hostel=hostel, image=image)
        return Response({"status": "Images uploaded"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def add_rules(self, request, pk=None):
        hostel = self.get_object()
        rules = request.data.get("rules", [])
        for rule_data in rules:
            HostelRule.objects.create(hostel=hostel, **rule_data)
        return Response({"status": "Rules added"}, status=status.HTTP_200_OK)
