from django.core.cache import cache
from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from .models import Home
from .serializers import HomeSerializer
from .permissions import *

# Pagination
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50

HOME_LIST_CACHE_KEY = "home_list_cache_user_{user_id}"
HOME_DETAIL_CACHE_PREFIX = "home_detail_{home_id}_user_{user_id}"

class UserHomeViewSet(viewsets.ModelViewSet):
    serializer_class = HomeSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsMessOwner,
        IsOwnerOfHome
    ]
    pagination_class = StandardResultsSetPagination

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_fields = ["city", "state"]
    search_fields = ["name", "address", "city", "state"]
    ordering_fields = ["created_at", "name"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            Home.objects.filter(owner=self.request.user, is_verified=True)
            .select_related("owner")
            .prefetch_related("images", "mess_menus")
        )

    def clear_home_cache(self, user_id, home_id=None):
        cache.delete(HOME_LIST_CACHE_KEY.format(user_id=user_id))
        if home_id:
            cache.delete(
                HOME_DETAIL_CACHE_PREFIX.format(
                    home_id=home_id,
                    user_id=user_id
                )
            )

    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        cache_key = HOME_LIST_CACHE_KEY.format(user_id=request.user.id)
        data = cache.get(cache_key)

        if not data:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(
                queryset, many=True, context={"homes": queryset}
            )
            data = serializer.data
            cache.set(cache_key, data, 60 * 5)

        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        home = self.get_object()
        cache_key = HOME_DETAIL_CACHE_PREFIX.format(
            home_id=home.id,
            user_id=request.user.id
        )

        data = cache.get(cache_key)
        if not data:
            serializer = self.get_serializer(
                home, context={"homes": [home]}
            )
            data = serializer.data
            cache.set(cache_key, data, 60 * 5)

        return Response(data)

    def perform_create(self, serializer):
        home = serializer.save(owner=self.request.user)
        self.clear_home_cache(self.request.user.id, home.id)

    def perform_update(self, serializer):
        home = serializer.save()
        self.clear_home_cache(self.request.user.id, home.id)

    def perform_destroy(self, instance):
        home_id = instance.id
        instance.delete()
        self.clear_home_cache(self.request.user.id, home_id)
