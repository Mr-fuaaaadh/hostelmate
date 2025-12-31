from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins, permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework import viewsets
from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from hostels.models import Hostel
from mess.models import Home
from .models import CustomUser
from django.core.cache import cache
from rest_framework.filters import SearchFilter, OrderingFilter
from .serializers import UserRegisterSerializer, LoggedUserDetailsSerializer, UserHostelDetailSerializer
from mess.serializers import HomeSerializer
# ---------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


# ---------------------------------------------------------------------
# USER VIEWSETS
# ---------------------------------------------------------------------
class UserRegisterViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    Allows new users to register.
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]


class UserProfileViewSet(mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin,
                         viewsets.GenericViewSet):
    """
    Retrieve or update the currently logged-in user's profile.
    """
    serializer_class = LoggedUserDetailsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
    

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50

HOSTEL_LIST_CACHE_KEY = "hostel_list_cache"
HOSTEL_DETAIL_CACHE_PREFIX = "hostel_detail_"

class UserHostelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    User-side viewset for hostels with rooms, facilities, and meal plans.
    """
    queryset = Hostel.objects.filter(is_active=True)\
        .select_related("owner")\
        .prefetch_related(
            "images",
            "hostel_facilities__facility",
            "rooms__images",
            "rooms__room_facilities__facility",
            "meal_plans",
            "delivery_areas"
        )
    serializer_class = UserHostelDetailSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["city", "state", "hostel_type"]
    search_fields = ["name", "address", "city", "state"]
    ordering_fields = ["available_rooms_count", "total_rooms_count", "created_at"]
    ordering = ["-created_at"]

    @method_decorator(cache_page(60*5, key_prefix=HOSTEL_LIST_CACHE_KEY))
    def list(self, request, *args, **kwargs):
        """
        Cached hostel list endpoint.
        """
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Cached hostel detail endpoint.
        """
        hostel = self.get_object()
        cache_key = f"{HOSTEL_DETAIL_CACHE_PREFIX}{hostel.id}"
        data = cache.get(cache_key)

        if not data:
            data = self.get_serializer(hostel).data
            data["availability_summary"] = hostel.availability_summary
            cache.set(cache_key, data, 60*5)  # cache for 5 minutes

        return Response(data)
    




MESS_LIST_CACHE_KEY = "mess_provider_list_cache"
MESS_DETAIL_CACHE_PREFIX = "mess_provider_detail_"

class MessProvidersViewSet(viewsets.ReadOnlyModelViewSet):
    """
    User-side Mess Providers API

    Features:
    - List & Detail
    - Pagination
    - Search
    - Filter
    - Sorting
    - Caching
    """

    serializer_class = HomeSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination

    # Filters
    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    # Search fields
    search_fields = [
        "name",
        "address",
        "city",
        "state",
        "description",
    ]

    # Filter fields
    filterset_fields = {
        "city": ["exact", "iexact"],
        "state": ["exact", "iexact"],
        "is_verified": ["exact"],
    }

    # Sorting
    ordering_fields = [
        "name",
        "city",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at"]

    def get_queryset(self):
        """
        IMPORTANT:
        Only relations that actually exist on Home are prefetched.
        """
        return (
            Home.objects
            .filter(is_verified=True)
            .select_related("owner")
            .prefetch_related(
                "images",        # FK related_name
                "mess_menus",    # GenericRelation
            )
        )

    @method_decorator(cache_page(60 * 5, key_prefix=MESS_LIST_CACHE_KEY))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        mess = self.get_object()
        cache_key = f"{MESS_DETAIL_CACHE_PREFIX}{mess.id}"
        data = cache.get(cache_key)

        if not data:
            data = self.get_serializer(mess).data
            cache.set(cache_key, data, 60 * 5)

        return Response(data)

