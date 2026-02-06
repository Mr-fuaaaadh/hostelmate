from rest_framework import serializers
from .models import Home, HomeImage, MessMenu, DeliveryArea, MealPlan, ProviderFeature
from django.contrib.contenttypes.models import ContentType


# -----------------------------
# Home Image Serializer
# -----------------------------
class HomeImageSerializer(serializers.ModelSerializer):
    home_id = serializers.PrimaryKeyRelatedField(
        queryset=Home.objects.all(),
        source="home",
        write_only=True
    )

    image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = HomeImage
        fields = [
            "id",
            "home_id",
            "image",
            "image_url",
            "alt_text",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None



# -----------------------------
# MessMenu Serializer
# -----------------------------
class MessMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessMenu
        fields = [
            "id", "day",
            "veg_breakfast", "veg_breakfast_accompaniment",
            "veg_lunch", "veg_lunch_accompaniment",
            "veg_dinner", "veg_dinner_accompaniment",
            "nonveg_breakfast", "nonveg_breakfast_accompaniment",
            "nonveg_lunch", "nonveg_lunch_accompaniment",
            "nonveg_dinner", "nonveg_dinner_accompaniment",
            "breakfast_image", "lunch_image", "dinner_image",
        ]


# -----------------------------
# Delivery Area Serializer
# -----------------------------
class DeliveryAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryArea
        fields = ["id", "area_name"]


# -----------------------------
# Meal Plan Serializer
# -----------------------------
class MealPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealPlan
        fields = ["id", "plan_id", "name", "price", "meals", "features"]


# -----------------------------
# Provider Feature Serializer
# -----------------------------
class ProviderFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderFeature
        fields = ["id", "icon", "title", "description"]


# -----------------------------
# Home Serializer (Full)
# -----------------------------
class HomeSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)
    images = HomeImageSerializer(many=True, read_only=True)
    mess_menus = MessMenuSerializer(many=True, read_only=True)

    delivery_areas = serializers.SerializerMethodField()
    meal_plans = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()

    class Meta:
        model = Home
        fields = [
            "id", "owner", "name", "cover_image", "address",
            "city", "state", "pincode", "description",
            "latitude", "longitude", "is_verified",
            "created_at", "updated_at",
            "images", "mess_menus",
            "delivery_areas", "meal_plans", "features",
        ]

    # ----------------------------
    # Generic FK resolvers
    # ----------------------------
    def get_delivery_areas(self, obj):
        content_type = ContentType.objects.get_for_model(Home)
        qs = DeliveryArea.objects.filter(
            provider_type=content_type,
            provider_id=obj.id
        )
        return DeliveryAreaSerializer(qs, many=True).data

    def get_meal_plans(self, obj):
        content_type = ContentType.objects.get_for_model(Home)
        qs = MealPlan.objects.filter(
            provider_type=content_type,
            provider_id=obj.id
        )
        return MealPlanSerializer(qs, many=True).data

    def get_features(self, obj):
        content_type = ContentType.objects.get_for_model(Home)
        qs = ProviderFeature.objects.filter(
            provider_type=content_type,
            provider_id=obj.id
        )
        return ProviderFeatureSerializer(qs, many=True).data








class HomeImageBulkUploadSerializer(serializers.Serializer):
    home_id = serializers.IntegerField()
    images = serializers.ListField(
        child=serializers.ImageField(),
        allow_empty=False
    )
    alt_texts = serializers.ListField(
        child=serializers.CharField(max_length=500),
        required=False
    )

    def validate(self, attrs):
        images = attrs["images"]
        alt_texts = attrs.get("alt_texts", [])

        if alt_texts and len(images) != len(alt_texts):
            raise serializers.ValidationError(
                "Images count and alt_texts count must match"
            )

        return attrs




class MessMenuBulkUploadSerializer(serializers.Serializer):
    day = serializers.ChoiceField(choices=MessMenu.DAY_CHOICES)
    
    # Veg meals
    veg_breakfast = serializers.CharField(required=False, allow_blank=True)
    veg_breakfast_accompaniment = serializers.CharField(required=False, allow_blank=True)
    veg_lunch = serializers.CharField(required=False, allow_blank=True)
    veg_lunch_accompaniment = serializers.CharField(required=False, allow_blank=True)
    veg_dinner = serializers.CharField(required=False, allow_blank=True)
    veg_dinner_accompaniment = serializers.CharField(required=False, allow_blank=True)

    # Non-veg meals
    nonveg_breakfast = serializers.CharField(required=False, allow_blank=True)
    nonveg_breakfast_accompaniment = serializers.CharField(required=False, allow_blank=True)
    nonveg_lunch = serializers.CharField(required=False, allow_blank=True)
    nonveg_lunch_accompaniment = serializers.CharField(required=False, allow_blank=True)
    nonveg_dinner = serializers.CharField(required=False, allow_blank=True)
    nonveg_dinner_accompaniment = serializers.CharField(required=False, allow_blank=True)

    # Meal images
    breakfast_image = serializers.ImageField(required=False)
    lunch_image = serializers.ImageField(required=False)
    dinner_image = serializers.ImageField(required=False)

    # Accept list of items
    def validate(self, attrs):
        return attrs
