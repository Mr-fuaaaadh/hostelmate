import logging

from rest_framework import viewsets, permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Hostel, HostelImage
from .serializers import HostelSerializer, HostelCreateUpdateSerializer
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
    permission_classes = [
        permissions.IsAuthenticated,
        IsOwnerOrReadOnly
    ]

    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser
    ]

    pagination_class = StandardResultsSetPagination  # ✅ ADD THIS LINE

    def get_queryset(self):
        queryset = Hostel.objects.filter(owner=self.request.user).select_related("owner").prefetch_related(
            "hostel_facilities__facility",
            "images",
            "rules",
            "rooms"
        )
        logger.info(
            f"User {self.request.user.id} accessed hostels - Count: {queryset.count()}"
        )
        return queryset

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return HostelCreateUpdateSerializer
        return HostelSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


