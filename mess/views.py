from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.contrib.contenttypes.models import ContentType
from .models import Home, DeliveryArea, MealPlan, ProviderFeature
from .serializers import HomeSerializer


# -----------------------------
# Pagination
# -----------------------------
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


# -----------------------------
# Cached & Optimized Home ViewSet
# -----------------------------
HOME_LIST_CACHE_KEY = "home_list_cache"
HOME_DETAIL_CACHE_PREFIX = "home_detail_"


class UserHomeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve Homes with related:
    - Images
    - Mess menus
    - Delivery areas
    - Meal plans
    - Features
    """
    serializer_class = HomeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["city", "state"]
    search_fields = ["name", "address", "city", "state"]
    ordering_fields = ["created_at", "name"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """
        Prefetch only valid relations:
        - FK: images
        - GenericRelation: mess_menus
        GenericFK relations are loaded in the serializer
        """
        return (
            Home.objects.filter(is_verified=True)
            .select_related("owner")
            .prefetch_related("images", "mess_menus")
        )

    # -----------------------------
    # Cached list
    # -----------------------------
    @method_decorator(cache_page(60 * 5, key_prefix=HOME_LIST_CACHE_KEY))
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # Pass queryset to serializer context for optimized GenericFK loading
        serializer = self.get_serializer(queryset, many=True, context={"homes": queryset})
        return Response(serializer.data)

    # -----------------------------
    # Cached detail
    # -----------------------------
    def retrieve(self, request, *args, **kwargs):
        home = self.get_object()
        cache_key = f"{HOME_DETAIL_CACHE_PREFIX}{home.id}"
        data = cache.get(cache_key)

        if not data:
            serializer = self.get_serializer(home, context={"homes": [home]})
            data = serializer.data
            cache.set(cache_key, data, 60 * 5)  # Cache for 5 minutes

        return Response(data)
