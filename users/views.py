import logging
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db.models import Q, Prefetch
from django.core.cache import cache

from rest_framework import viewsets, mixins, permissions, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend

from hostels.models import Hostel
from mess.models import Home
from .models import CustomUser
from .serializers import UserRegisterSerializer, LoggedUserDetailsSerializer, UserHostelDetailSerializer
from mess.serializers import HomeSerializer

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# Configuration & Constants
# ---------------------------------------------------------------------
CACHE_TIMEOUT = 60 * 5  # 5 minutes
HOSTEL_LIST_CACHE_KEY = "hostel_list_cache"
HOSTEL_DETAIL_CACHE_PREFIX = "hostel_detail_"
MESS_LIST_CACHE_KEY = "mess_provider_list_cache"
MESS_DETAIL_CACHE_PREFIX = "mess_provider_detail_"


# ---------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------
class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination for data lists.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


# ---------------------------------------------------------------------
# USER VIEWSETS
# ---------------------------------------------------------------------

class UserRegisterViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    Public endpoint for new user registration.
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]


class UserProfileViewSet(mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin,
                         viewsets.GenericViewSet):
    """
    Endpoint for authenticated users to view or update their own profile.
    """
    serializer_class = LoggedUserDetailsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """
        Always returns the current authenticated user.
        """
        return self.request.user


class UserHostelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    User-facing API for browsing hostels with optimized data loading and caching.
    """
    queryset = Hostel.objects.filter(is_active=True).select_related("owner").prefetch_related(
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

    @method_decorator(cache_page(CACHE_TIMEOUT, key_prefix=HOSTEL_LIST_CACHE_KEY))
    def list(self, request, *args, **kwargs):
        """
        Returns a cached list of active hostels.
        """
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Returns cached hostel details, including an availability summary.
        """
        hostel = self.get_object()
        cache_key = f"{HOSTEL_DETAIL_CACHE_PREFIX}{hostel.id}"

        def get_data():
            serializer = self.get_serializer(hostel)
            data = serializer.data
            data["availability_summary"] = hostel.availability_summary
            return data

        data = cache.get_or_set(cache_key, get_data, CACHE_TIMEOUT)
        return Response(data)


class MessProvidersViewSet(viewsets.ReadOnlyModelViewSet):
    """
    User-facing API for browsing mess providers with search, filtering, and caching.
    """
    serializer_class = HomeSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "address", "city", "state", "description"]
    filterset_fields = {
        "city": ["exact", "iexact"],
        "state": ["exact", "iexact"],
        "is_verified": ["exact"],
    }
    ordering_fields = ["name", "city", "created_at", "updated_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """
        Limits results to verified providers and optimizes relationship loading.
        """
        return Home.objects.filter(is_verified=True).select_related("owner").prefetch_related(
            "images",
            "mess_menus"
        )

    @method_decorator(cache_page(CACHE_TIMEOUT, key_prefix=MESS_LIST_CACHE_KEY))
    def list(self, request, *args, **kwargs):
        """
        Returns a cached list of verified mess providers.
        """
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Returns cached details for a specific mess provider.
        """
        mess = self.get_object()
        cache_key = f"{MESS_DETAIL_CACHE_PREFIX}{mess.id}"
        
        data = cache.get_or_set(
            cache_key, 
            lambda: self.get_serializer(mess).data, 
            CACHE_TIMEOUT
        )
        return Response(data)


class UnifiedSearchSuggestionAPIView(APIView):
    """
    API endpoint for real-time search suggestions across hostels and mess providers.
    Uses caching for performance.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get("q", "").strip()

        if len(query) < 2:
            return Response([])

        cache_key = f"search_suggestions_{query.lower()}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        results = []

        # Optimized Hostels Search
        hostels = Hostel.objects.filter(is_active=True).filter(
            Q(name__icontains=query) | Q(city__icontains=query)
        ).only("id", "name", "city", "description")[:5]

        for hostel in hostels:
            results.append({
                "id": hostel.id,
                "type": "hostel",
                "name": hostel.name,
                "city": hostel.city,
                "description": hostel.description[:120] if hostel.description else "",
            })

        # Optimized Mess Providers Search
        messes = Home.objects.filter(is_verified=True).filter(
            Q(name__icontains=query) | Q(city__icontains=query)
        ).prefetch_related("images").only("id", "name", "city", "description")[:5]

        for mess in messes:
            first_image = mess.images.first()
            image_url = first_image.image.url if first_image else None
            
            results.append({
                "id": mess.id,
                "type": "mess",
                "name": mess.name,
                "city": mess.city,
                "description": mess.description[:120] if mess.description else "",
                "image": image_url,
            })

        cache.set(cache_key, results, CACHE_TIMEOUT)
        return Response(results)

