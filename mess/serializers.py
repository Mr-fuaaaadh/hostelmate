from rest_framework import serializers
from .models import Home, HomeImage, MessMenu, DeliveryArea, MealPlan, ProviderFeature
from django.contrib.contenttypes.models import ContentType


# -----------------------------
# Home Image Serializer
# -----------------------------
class HomeImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeImage
        fields = ["id", "image", "alt_text", "created_at"]


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

