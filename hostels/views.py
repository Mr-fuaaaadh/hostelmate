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


import logging

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response

from .models import Hostel, HostelFacility, HostelImage, HostelRule
from .serializers import (
    HostelSerializer,
    HostelCreateUpdateSerializer,
)
from .permissions import IsOwnerOrReadOnly

logger = logging.getLogger(__name__)


# -----------------------------------
# Pagination
# -----------------------------------
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


# -----------------------------------
# Hostel ViewSet
# -----------------------------------
class HostelViewSet(viewsets.ModelViewSet):
    """
    Hostel CRUD + facilities + rules + images
    Only hostel owner can access/edit
    """

    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    pagination_class = StandardResultsSetPagination
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = ["city", "state", "is_verified", "hostel_type"]
    search_fields = ["name", "address", "city", "state"]
    ordering_fields = ["id", "created_at", "name"]
    ordering = ["-created_at"]

    # -----------------------------------
    # Queryset
    # -----------------------------------
    def get_queryset(self):
        queryset = (
            Hostel.objects.filter(owner=self.request.user)
            .select_related("owner")
            .prefetch_related(
                "hostel_facilities__facility",
                "images",
                "rules",
            )
        )

        logger.info(
            f"User {self.request.user} accessed hostels: {[h.id for h in queryset]}"
        )
        return queryset

    # -----------------------------------
    # Serializer selection
    # -----------------------------------
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return HostelCreateUpdateSerializer
        return HostelSerializer

    # -----------------------------------
    # Create
    # -----------------------------------
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    # -----------------------------------
    # Add Images (Multiple)
    # -----------------------------------
    @action(
        detail=True,
        methods=["post"],
        parser_classes=[MultiPartParser, FormParser],
    )
    def add_images(self, request, pk=None):
        hostel = self.get_object()
        images = request.FILES.getlist("images")

        if not images:
            return Response(
                {"error": "No images provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        HostelImage.objects.bulk_create(
            [
                HostelImage(hostel=hostel, image=image)
                for image in images
            ]
        )

        return Response(
            {"status": "Images uploaded successfully"},
            status=status.HTTP_201_CREATED,
        )

