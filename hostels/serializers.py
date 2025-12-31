from rest_framework import serializers
from .models import Hostel, HostelImage, HostelFacility, HostelRule
from rooms.models import Facility
from rooms.serializers import RoomSerializer
from mess.serializers import MessMenuSerializer
from mess.models import MessMenu
from django.contrib.contenttypes.models import ContentType
from django.db import transaction



# -----------------------------
# Facility Serializer
# -----------------------------
class FacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Facility
        fields = ["id", "name", "slug"]


# -----------------------------
# Hostel Facility Serializer
# -----------------------------
class HostelFacilitySerializer(serializers.ModelSerializer):
    facility = FacilitySerializer(read_only=True)
    facility_id = serializers.PrimaryKeyRelatedField(
        queryset=Facility.objects.all(),
        source="facility",
        write_only=True
    )

    class Meta:
        model = HostelFacility
        fields = ["id", "facility", "facility_id"]



# -----------------------------
# Hostel Image Serializer
# -----------------------------
class HostelImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = HostelImage
        fields = ["id", "image", "caption", "is_cover", "order", "is_active"]


# -----------------------------
# Hostel Rule Serializer
# -----------------------------
class HostelRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = HostelRule
        fields = ["id", "title", "description", "rule_type", "is_active"]



# -----------------------------
# Hostel Serializer (Full)
# -----------------------------
class HostelSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)
    hostel_facilities = HostelFacilitySerializer(many=True, read_only=True)
    images = HostelImageSerializer(many=True, read_only=True)
    rules = HostelRuleSerializer(many=True, read_only=True)
    rooms = RoomSerializer(many=True, read_only=True)
    available_rooms = serializers.IntegerField(source="available_rooms_count", read_only=True)
    total_rooms = serializers.IntegerField(source="total_rooms_count", read_only=True)
    availability_summary = serializers.CharField(read_only=True)
    mess_menu = serializers.SerializerMethodField()

    class Meta:
        model = Hostel
        fields = [
            "id", "owner", "name", "description", "address",
            "city", "state", "pincode", "hostel_type",
            "latitude", "longitude", "is_verified", "is_active",
            "created_at", "updated_at",
            "hostel_facilities", "images", "rules",
            "rooms",
            "mess_menu",
            "available_rooms", "total_rooms", "availability_summary",
        ]


    def get_mess_menu(self, obj):
        content_type = ContentType.objects.get_for_model(Hostel)
        menus = MessMenu.objects.filter(
            content_type=content_type,
            object_id=obj.id
        ).order_by("id")

        return MessMenuSerializer(menus, many=True).data


# -----------------------------
# Hostel Create / Update Serializer
# -----------------------------
class HostelCreateUpdateSerializer(serializers.ModelSerializer):
    hostel_facilities = HostelFacilitySerializer(many=True, required=True)
    images = HostelImageSerializer(many=True, required=True)
    rules = HostelRuleSerializer(many=True, required=True)

    class Meta:
        model = Hostel
        exclude = ["owner", "created_at", "updated_at"]

    @transaction.atomic
    def create(self, validated_data):
        facilities_data = validated_data.pop("hostel_facilities", [])
        images_data = validated_data.pop("images", [])
        rules_data = validated_data.pop("rules", [])

        # ✅ OWNER IS SET IN VIEWSET ONLY
        hostel = Hostel.objects.create(**validated_data)

        for facility in facilities_data:
            HostelFacility.objects.create(hostel=hostel, **facility)

        for image in images_data:
            HostelImage.objects.create(hostel=hostel, **image)

        for rule in rules_data:
            HostelRule.objects.create(hostel=hostel, **rule)

        return hostel

    @transaction.atomic
    def update(self, instance, validated_data):
        facilities_data = validated_data.pop("hostel_facilities", None)
        images_data = validated_data.pop("images", None)
        rules_data = validated_data.pop("rules", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if facilities_data is not None:
            instance.hostel_facilities.all().delete()
            HostelFacility.objects.bulk_create([
                HostelFacility(hostel=instance, **f)
                for f in facilities_data
            ])

        if images_data is not None:
            instance.images.all().delete()
            HostelImage.objects.bulk_create([
                HostelImage(hostel=instance, **i)
                for i in images_data
            ])

        if rules_data is not None:
            instance.rules.all().delete()
            HostelRule.objects.bulk_create([
                HostelRule(hostel=instance, **r)
                for r in rules_data
            ])

        return instance

