from rest_framework import serializers
from .models import Hostel, HostelImage, HostelFacility, HostelRule
from rooms.models import Facility, Room
from rooms.serializers import RoomSerializer
from mess.serializers import MessMenuSerializer
from mess.models import MessMenu
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
import json


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


class HostelCreateUpdateSerializer(serializers.ModelSerializer):
    facilities = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    rules = serializers.CharField(write_only=True, required=False)
    rooms = serializers.CharField(write_only=True, required=False)
    mess = serializers.CharField(write_only=True, required=False)

    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Hostel
        fields = [
            "name", "description", "address",
            "city", "state", "pincode",
            "hostel_type", "latitude", "longitude",
            "facilities", "rules", "rooms", "mess",
            "images",
        ]

    def create(self, validated_data):
        facilities = validated_data.pop("facilities", [])
        rules_raw = validated_data.pop("rules", "[]")
        rooms_raw = validated_data.pop("rooms", "[]")
        mess_raw = validated_data.pop("mess", "[]")
        images = validated_data.pop("images", [])

        try:
            rules = json.loads(rules_raw)
            rooms = json.loads(rooms_raw)
            mess = json.loads(mess_raw)
        except json.JSONDecodeError:
            raise serializers.ValidationError("Invalid JSON format")

        hostel = Hostel.objects.create(**validated_data)

        # Facilities
        HostelFacility.objects.bulk_create([
            HostelFacility(hostel=hostel, facility_id=fid)
            for fid in facilities
        ])

        # Rules
        HostelRule.objects.bulk_create([
            HostelRule(
                hostel=hostel,
                title=r["title"],
                description=r["description"],
                rule_type=r.get("rule_type", "general")
            ) for r in rules
        ])

        # Rooms
        Room.objects.bulk_create([
            Room(
                hostel=hostel,
                room_number=room["room_number"],
                room_type=room["room_type"],
                capacity=room["capacity"],
                daily_price=room["daily_price"],
                monthly_price=room["monthly_price"],
                description=room.get("description", "")
            ) for room in rooms
        ])

        # Mess Menu
        content_type = ContentType.objects.get_for_model(Hostel)
        MessMenu.objects.bulk_create([
            MessMenu(
                content_type=content_type,
                object_id=hostel.id,
                day=m["day"],
                veg_breakfast=m.get("veg_breakfast"),
                veg_lunch=m.get("veg_lunch"),
                veg_dinner=m.get("veg_dinner"),
                nonveg_breakfast=m.get("nonveg_breakfast"),
                nonveg_lunch=m.get("nonveg_lunch"),
                nonveg_dinner=m.get("nonveg_dinner"),
            ) for m in mess
        ])

        # Images
        HostelImage.objects.bulk_create([
            HostelImage(hostel=hostel, image=image)
            for image in images
        ])

        return hostel
