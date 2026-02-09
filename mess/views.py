from django.core.cache import cache
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from .models import Home, HomeImage, MessMenu
from django.core.exceptions import PermissionDenied, ValidationError
from django.contrib.contenttypes.models import ContentType
from .serializers import HomeSerializer, HomeImageSerializer, HomeImageBulkUploadSerializer, MessMenuSerializer, MessMenuBulkUploadSerializer
from .permissions import *
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

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



class HomeImageViewSet(viewsets.ModelViewSet):
    serializer_class = HomeImageSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsOwnerOfHomeImage,
    ]

    def get_queryset(self):
        """
        List images only for homes owned by the logged-in user
        Optional filter: ?home_id=1
        """
        queryset = HomeImage.objects.filter(
            home__owner=self.request.user
        ).select_related("home")

        home_id = self.request.query_params.get("home_id")
        if home_id:
            queryset = queryset.filter(home_id=home_id)

        return queryset

    def perform_create(self, serializer):
        home = serializer.validated_data["home"]

        if home.owner != self.request.user:
            raise PermissionError("You do not own this home")

        serializer.save()
    
    @action(detail=False, methods=["post"], url_path="bulk-upload")
    def bulk_upload(self, request):
        serializer = HomeImageBulkUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        home = get_object_or_404(
            Home,
            id=serializer.validated_data["home_id"],
            owner=request.user
        )

        images = serializer.validated_data["images"]
        alt_texts = serializer.validated_data.get("alt_texts", [])

        objs = []
        for index, image in enumerate(images):
            objs.append(
                HomeImage(
                    home=home,
                    image=image,
                    alt_text=alt_texts[index] if alt_texts else ""
                )
            )

        HomeImage.objects.bulk_create(objs)

        return Response(
            {"message": f"{len(objs)} images uploaded successfully"},
            status=status.HTTP_201_CREATED
        )





class MessMenuViewSet(viewsets.ModelViewSet):
    serializer_class = MessMenuSerializer
    permission_classes = [permissions.IsAuthenticated]

    # -------------------
    # QUERYSET
    # -------------------
    def get_queryset(self):
        home_ct = ContentType.objects.get_for_model(Home)

        return MessMenu.objects.filter(
            content_type=home_ct,
            object_id__in=Home.objects.filter(
                owner=self.request.user
            ).values_list("id", flat=True)
        ).select_related("content_type")

    # -------------------
    # CREATE (UPSERT)
    # -------------------
    def perform_create(self, serializer):
        home = Home.objects.filter(owner=self.request.user).first()
        if not home:
            raise ValidationError("No home found for this user")

        content_type = ContentType.objects.get_for_model(Home)
        day = serializer.validated_data["day"]

        existing_menu = MessMenu.objects.filter(
            content_type=content_type,
            object_id=home.id,
            day=day
        ).first()

        if existing_menu:
            for attr, value in serializer.validated_data.items():
                setattr(existing_menu, attr, value)
            existing_menu.save()
            serializer.instance = existing_menu
        else:
            serializer.save(
                content_type=content_type,
                object_id=home.id
            )

    # -------------------
    # UPDATE
    # -------------------
    def perform_update(self, serializer):
        instance = self.get_object()
        home = Home.objects.filter(owner=self.request.user).first()

        if not home or instance.object_id != home.id:
            raise PermissionDenied("You do not own this home")

        serializer.save()

    # -------------------
    # DELETE
    # -------------------
    def perform_destroy(self, instance):
        home = Home.objects.filter(owner=self.request.user).first()

        if not home or instance.object_id != home.id:
            raise PermissionDenied("You do not own this home")

        instance.delete()

    # -------------------
    # BULK UPLOAD (SAFE)
    # -------------------
    @action(detail=False, methods=["post"], url_path="bulk-upload")
    def bulk_upload(self, request):
        menus = request.data.get("menus", [])
        if not menus:
            return Response({"error": "No menus provided"},status=status.HTTP_400_BAD_REQUEST)
        home_ct = ContentType.objects.get_for_model(Home)
        created = 0
        updated = 0

        for menu_data in menus:
            serializer = MessMenuBulkUploadSerializer(data=menu_data)
            serializer.is_valid(raise_exception=True)
            validated = serializer.validated_data
            home = get_object_or_404(Home, owner=request.user)
            day = validated.pop("day")
            menu, is_created = MessMenu.objects.update_or_create(content_type=home_ct,object_id=home.pk,day=day,defaults=validated)
            created += int(is_created)
            updated += int(not is_created)

        return Response(
            {
                "created": created,
                "updated": updated
            },
            status=status.HTTP_200_OK
        )




