from rest_framework import serializers
from .models import Hostel, HostelImage, HostelFacility, HostelRule
from rooms.models import Facility, Room
from rooms.serializers import RoomReadSerializer
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
    rooms = RoomReadSerializer(many=True, read_only=True)
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
    """
    Production-ready serializer for Hostel Create & Update
    Supports multipart/form-data with images + nested JSON
    """

    # JSON fields (sent as STRING in form-data)
    facilities = serializers.CharField(write_only=True, required=True)
    rules = serializers.CharField(write_only=True, required=True)
    rooms = serializers.CharField(write_only=True, required=True)
    mess = serializers.CharField(write_only=True, required=True)

    # Image uploads
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=True
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

    # ======================================================
    # 🔒 JSON PARSERS (REUSABLE & SAFE)
    # ======================================================

    def _parse_json(self, value, field_name, expect_dict=True):
        """
        Parse JSON string and validate structure
        """
        try:
            data = json.loads(value)
        except json.JSONDecodeError:
            raise serializers.ValidationError({
                field_name: "Invalid JSON format"
            })

        if not isinstance(data, list):
            raise serializers.ValidationError({
                field_name: "Must be a JSON array"
            })

        if expect_dict:
            for item in data:
                if not isinstance(item, dict):
                    raise serializers.ValidationError({
                        field_name: "Each item must be an object"
                    })

        return data

    def _parse_int_list(self, value, field_name):
        """
        Parse JSON array of integers
        """
        try:
            data = json.loads(value)
        except json.JSONDecodeError:
            raise serializers.ValidationError({
                field_name: "Invalid JSON format"
            })

        if not isinstance(data, list) or not all(isinstance(i, int) for i in data):
            raise serializers.ValidationError({
                field_name: "Must be a list of integers"
            })

        return data

    # ======================================================
    # ✅ FIELD VALIDATIONS
    # ======================================================

    def validate_facilities(self, value):
        return self._parse_int_list(value, "facilities")

    def validate_rules(self, value):
        return self._parse_json(value, "rules")

    def validate_rooms(self, value):
        rooms = self._parse_json(value, "rooms")

        for room in rooms:
            if not room.get("room_number"):
                raise serializers.ValidationError(
                    "Each room must have a room_number"
                )
            if room.get("capacity", 0) <= 0:
                raise serializers.ValidationError(
                    "Room capacity must be greater than 0"
                )
        return rooms

    def validate_mess(self, value):
        return self._parse_json(value, "mess")

    # ======================================================
    # 🧱 CREATE
    # ======================================================

    @transaction.atomic
    def create(self, validated_data):
        facilities = validated_data.pop("facilities")  # list[int]
        rules = validated_data.pop("rules")            # list[dict]
        rooms = validated_data.pop("rooms")            # list[dict]
        mess = validated_data.pop("mess")               # list[dict]
        images = validated_data.pop("images")

        hostel = Hostel.objects.create(**validated_data)

        # ------------------ Facilities ------------------
        HostelFacility.objects.bulk_create([
            HostelFacility(hostel=hostel, facility_id=fid)
            for fid in facilities
        ])

        # ------------------ Rules ------------------
        HostelRule.objects.bulk_create([
            HostelRule(
                hostel=hostel,
                title=r["title"],
                description=r.get("description", ""),
                rule_type=r.get("rule_type", "general")
            )
            for r in rules
        ])

        # ------------------ Rooms ------------------
        room_objs = []
        total_capacity = 0

        for room in rooms:
            capacity = room.get("capacity", 1)
            total_capacity += capacity

            room_objs.append(Room(
                hostel=hostel,
                room_number=room["room_number"],
                room_type=room.get("room_type"),
                capacity=capacity,
                daily_price=room.get("daily_price"),
                monthly_price=room.get("monthly_price"),
                description=room.get("description", "")
            ))

        Room.objects.bulk_create(room_objs)

        hostel.total_rooms_count = len(room_objs)
        hostel.available_rooms_count = total_capacity
        hostel.save(update_fields=[
            "total_rooms_count",
            "available_rooms_count"
        ])

        # ------------------ Mess Menu ------------------
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
            )
            for m in mess
        ])

        # ------------------ Images ------------------
        HostelImage.objects.bulk_create([
            HostelImage(hostel=hostel, image=image)
            for image in images
        ])

        return hostel
    

    @transaction.atomic
    def update(self, instance, validated_data):

        facilities = validated_data.pop("facilities", None)
        rules = validated_data.pop("rules", None)
        rooms = validated_data.pop("rooms", None)
        mess = validated_data.pop("mess", None)
        images = validated_data.pop("images", None)

        # ------------------ Update base hostel fields ------------------
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # ------------------ Facilities ------------------
        if facilities is not None:
            HostelFacility.objects.filter(hostel=instance).delete()
            HostelFacility.objects.bulk_create([
                HostelFacility(hostel=instance, facility_id=fid)
                for fid in facilities
            ])

        # ------------------ Rules ------------------
        if rules is not None:
            HostelRule.objects.filter(hostel=instance).delete()
            HostelRule.objects.bulk_create([
                HostelRule(
                    hostel=instance,
                    title=r["title"],
                    description=r.get("description", ""),
                    rule_type=r.get("rule_type", "general")
                )
                for r in rules
            ])

        # ------------------ Rooms ------------------
        if rooms is not None:
            Room.objects.filter(hostel=instance).delete()

            room_objs = []
            total_capacity = 0

            for room in rooms:
                capacity = room.get("capacity", 1)
                total_capacity += capacity

                room_objs.append(Room(
                    hostel=instance,
                    room_number=room["room_number"],
                    room_type=room.get("room_type"),
                    capacity=capacity,
                    daily_price=room.get("daily_price"),
                    monthly_price=room.get("monthly_price"),
                    description=room.get("description", "")
                ))

            Room.objects.bulk_create(room_objs)

            instance.total_rooms_count = len(room_objs)
            instance.available_rooms_count = total_capacity
            instance.save(update_fields=[
                "total_rooms_count",
                "available_rooms_count"
            ])

        # ------------------ Mess ------------------
        if mess is not None:
            content_type = ContentType.objects.get_for_model(Hostel)
            MessMenu.objects.filter(
                content_type=content_type,
                object_id=instance.id
            ).delete()

            MessMenu.objects.bulk_create([
                MessMenu(
                    content_type=content_type,
                    object_id=instance.id,
                    day=m["day"],
                    veg_breakfast=m.get("veg_breakfast"),
                    veg_lunch=m.get("veg_lunch"),
                    veg_dinner=m.get("veg_dinner"),
                    nonveg_breakfast=m.get("nonveg_breakfast"),
                    nonveg_lunch=m.get("nonveg_lunch"),
                    nonveg_dinner=m.get("nonveg_dinner"),
                )
                for m in mess
            ])

        # ------------------ Images (append) ------------------
        if images:
            HostelImage.objects.bulk_create([
                HostelImage(hostel=instance, image=image)
                for image in images
            ])

        return instance


