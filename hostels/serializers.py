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

    @transaction.atomic
    def create(self, validated_data):
        facilities = validated_data.pop("facilities", [])
        rules_raw = validated_data.pop("rules", "[]")
        rooms_raw = validated_data.pop("rooms", "[]")
        mess_raw = validated_data.pop("mess", "[]")
        images = validated_data.pop("images", [])


        try:
            rules = json.loads(rules_raw) if isinstance(rules_raw, str) else rules_raw
            rooms = json.loads(rooms_raw) if isinstance(rooms_raw, str) else rooms_raw
            mess = json.loads(mess_raw) if isinstance(mess_raw, str) else mess_raw
        except json.JSONDecodeError:
            raise serializers.ValidationError({"error": "Invalid JSON format in nested fields"})

        hostel = Hostel.objects.create(**validated_data)

        # Facilities
        if facilities:
            HostelFacility.objects.bulk_create([
                HostelFacility(hostel=hostel, facility_id=fid)
                for fid in facilities
            ])

        # Rules
        if rules:
            HostelRule.objects.bulk_create([
                HostelRule(
                    hostel=hostel,
                    title=r.get("title"),
                    description=r.get("description"),
                    rule_type=r.get("rule_type", "general")
                ) for r in rules if r.get("title")
            ])

        # Rooms
        total_rooms = 0
        total_capacity = 0
        if rooms:
            room_objs = []
            for room in rooms:
                room_objs.append(Room(
                    hostel=hostel,
                    room_number=room.get("room_number"),
                    room_type=room.get("room_type"),
                    capacity=room.get("capacity", 1),
                    daily_price=room.get("daily_price"),
                    monthly_price=room.get("monthly_price"),
                    description=room.get("description", "")
                ))
                total_rooms += 1
                total_capacity += room.get("capacity", 1)
            Room.objects.bulk_create(room_objs)
            
            # Update hostel room counts
            hostel.total_rooms_count = total_rooms
            hostel.available_rooms_count = total_capacity # Assuming all are available initially
            hostel.save(update_fields=["total_rooms_count", "available_rooms_count"])

        # Mess Menu
        if mess:
            content_type = ContentType.objects.get_for_model(Hostel)
            MessMenu.objects.bulk_create([
                MessMenu(
                    content_type=content_type,
                    object_id=hostel.id,
                    day=m.get("day"),
                    veg_breakfast=m.get("veg_breakfast"),
                    veg_lunch=m.get("veg_lunch"),
                    veg_dinner=m.get("veg_dinner"),
                    nonveg_breakfast=m.get("nonveg_breakfast"),
                    nonveg_lunch=m.get("nonveg_lunch"),
                    nonveg_dinner=m.get("nonveg_dinner"),
                ) for m in mess if m.get("day")
            ])

        # Images - Use loop to trigger signals/custom save logic if any
        if images:
            for image in images:
                HostelImage.objects.create(hostel=hostel, image=image)

        return hostel

    @transaction.atomic
    def update(self, instance, validated_data):
        facilities = validated_data.pop("facilities", None)
        rules_raw = validated_data.pop("rules", None)
        rooms_raw = validated_data.pop("rooms", None)
        mess_raw = validated_data.pop("mess", None)
        images = validated_data.pop("images", None)


        # Update base hostel fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Handle Facilities
        if facilities is not None:
            instance.hostel_facilities.all().delete()
            HostelFacility.objects.bulk_create([
                HostelFacility(hostel=instance, facility_id=fid)
                for fid in facilities
            ])

        # Handle Rules
        if rules_raw is not None:
            try:
                rules = json.loads(rules_raw) if isinstance(rules_raw, str) else rules_raw
                instance.rules.all().delete()
                HostelRule.objects.bulk_create([
                    HostelRule(
                        hostel=instance,
                        title=r.get("title"),
                        description=r.get("description"),
                        rule_type=r.get("rule_type", "general")
                    ) for r in rules if r.get("title")
                ])
            except (json.JSONDecodeError, TypeError):
                pass

        # Handle Rooms
        if rooms_raw is not None:
            try:
                rooms = json.loads(rooms_raw) if isinstance(rooms_raw, str) else rooms_raw
                instance.rooms.all().delete()
                room_objs = []
                total_rooms = 0
                total_capacity = 0
                for room in rooms:
                    room_objs.append(Room(
                        hostel=instance,
                        room_number=room.get("room_number"),
                        room_type=room.get("room_type"),
                        capacity=room.get("capacity", 1),
                        daily_price=room.get("daily_price"),
                        monthly_price=room.get("monthly_price"),
                        description=room.get("description", "")
                    ))
                    total_rooms += 1
                    total_capacity += room.get("capacity", 1)
                Room.objects.bulk_create(room_objs)
                
                instance.total_rooms_count = total_rooms
                instance.available_rooms_count = total_capacity
                instance.save(update_fields=["total_rooms_count", "available_rooms_count"])
            except (json.JSONDecodeError, TypeError):
                pass

        # Handle Mess Menu
        if mess_raw is not None:
            try:
                mess = json.loads(mess_raw) if isinstance(mess_raw, str) else mess_raw
                content_type = ContentType.objects.get_for_model(Hostel)
                MessMenu.objects.filter(content_type=content_type, object_id=instance.id).delete()
                MessMenu.objects.bulk_create([
                    MessMenu(
                        content_type=content_type,
                        object_id=instance.id,
                        day=m.get("day"),
                        veg_breakfast=m.get("veg_breakfast"),
                        veg_lunch=m.get("veg_lunch"),
                        veg_dinner=m.get("veg_dinner"),
                        nonveg_breakfast=m.get("nonveg_breakfast"),
                        nonveg_lunch=m.get("nonveg_lunch"),
                        nonveg_dinner=m.get("nonveg_dinner"),
                    ) for m in mess if m.get("day")
                ])
            except (json.JSONDecodeError, TypeError):
                pass

        # Handle Images (Append new images)
        if images:
            for image in images:
                HostelImage.objects.create(hostel=instance, image=image)

        return instance
