from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from .models import Home
from .serializers import HomeSerializer

# -----------------------------
# Pagination
# -----------------------------
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


# -----------------------------
# User-Side Home Viewset
# -----------------------------
class UserHomeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve Homes with Mess menus, delivery areas, meal plans, and features.
    """
    queryset = Home.objects.filter(is_verified=True)\
        .select_related("owner")\
        .prefetch_related(
            "images",
            "mess_menus",
            "delivery_areas",
            "meal_plans",
            "features",
        )
    serializer_class = HomeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["city", "state"]
    search_fields = ["name", "address", "city", "state"]
    ordering_fields = ["created_at", "name"]
    ordering = ["-created_at"]

    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        """
        Cached list endpoint for performance.
        """
        return super().list(request, *args, **kwargs)
