from rest_framework import serializers
from .models import Room, Facility, RoomImage, RoomFacility
from django.db import transaction

# Facility Serializer
class FacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Facility
        fields = ["id", "name", "slug"]

# -----------------------------
# Read Serializers (Optimized for Output)
# -----------------------------

class RoomImageReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomImage
        fields = ["id", "image", "caption", "is_cover", "order"]

class RoomImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomImage
        fields = ["id", "room", "image", "caption", "is_cover", "order", "is_active", "created_at"]

class RoomFacilityReadSerializer(serializers.ModelSerializer):
    facility = FacilitySerializer(read_only=True)
    class Meta:
        model = RoomFacility
        fields = ["id", "facility"]

class RoomReadSerializer(serializers.ModelSerializer):
    """
    Detailed output serializer with prefetched nesting.
    """
    images = RoomImageReadSerializer(many=True, read_only=True)
    room_facilities = RoomFacilityReadSerializer(many=True, read_only=True)
    hostel_name = serializers.CharField(source="hostel.name", read_only=True)

    class Meta:
        model = Room
        fields = [
            "id", "hostel", "hostel_name", "room_number", "room_type",
            "is_available", "capacity", "daily_price", "monthly_price",
            "description", "images", "room_facilities"
        ]

# -----------------------------
# Write Serializers (Optimized for Input)
# -----------------------------

class RoomWriteSerializer(serializers.ModelSerializer):
    """
    Production-standard write serializer.
    Handles flat ID lists for facilities and binary file uploads for images.
    """
    facility_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of Facility IDs"
    )
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
        help_text="Multiple binary image files"
    )

    class Meta:
        model = Room
        fields = [
            "hostel", "room_number", "room_type", "is_available",
            "capacity", "daily_price", "monthly_price", "description",
            "facility_ids", "uploaded_images"
        ]

    @transaction.atomic
    def create(self, validated_data):
        facility_ids = validated_data.pop("facility_ids", [])
        uploaded_images = validated_data.pop("uploaded_images", [])
        room = Room.objects.create(**validated_data)

        # Bulk create relationship entries
        if facility_ids:
            RoomFacility.objects.bulk_create([
                RoomFacility(room=room, facility_id=fid)
                for fid in facility_ids
            ])

        # Handle image uploads
        if uploaded_images:
            for image in uploaded_images:
                RoomImage.objects.create(room=room, image=image)

        return room

    @transaction.atomic
    def update(self, instance, validated_data):
        facility_ids = validated_data.pop("facility_ids", None)
        uploaded_images = validated_data.pop("uploaded_images", None)

        # Update base fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update Facilities (Replace logic)
        if facility_ids is not None:
            instance.room_facilities.all().delete()
            RoomFacility.objects.bulk_create([
                RoomFacility(room=instance, facility_id=fid)
                for fid in facility_ids
            ])

        # Append new images
        if uploaded_images:
            for image in uploaded_images:
                RoomImage.objects.create(room=instance, image=image)

        return instance
