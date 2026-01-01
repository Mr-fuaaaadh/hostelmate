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
    rules = HostelRuleSerializer(many=True, required=True)

    class Meta:
        model = Hostel
        exclude = ["owner", "created_at", "updated_at"]

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]

        facilities_data = validated_data.pop("hostel_facilities", [])
        rules_data = validated_data.pop("rules", [])

        images = request.FILES.getlist("images")
        hostel = Hostel.objects.create(**validated_data)
        HostelFacility.objects.bulk_create([
            HostelFacility(hostel=hostel, **facility)
            for facility in facilities_data
        ])

        HostelRule.objects.bulk_create([
            HostelRule(hostel=hostel, **rule)
            for rule in rules_data
        ])

        HostelImage.objects.bulk_create([
            HostelImage(hostel=hostel, image=image)
            for image in images
        ])

        return hostel


