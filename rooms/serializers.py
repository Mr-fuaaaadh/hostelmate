from rest_framework import serializers
from .models import Room, Facility, RoomImage, RoomFacility
from django.db import transaction

# Facility Serializer
class FacilitySerializer(serializers.ModelSerializer):
    """
    Serializer for room facilities.
    """
    class Meta:
        model = Facility
        fields = ["id", "name", "slug"]


# -----------------------------
# Read Serializers (Optimized for Output)
# -----------------------------

class RoomImageReadSerializer(serializers.ModelSerializer):
    """
    Optimized image serializer for room detail/list views.
    """
    class Meta:
        model = RoomImage
        fields = ["id", "image", "caption", "is_cover", "order"]


class RoomImageSerializer(serializers.ModelSerializer):
    """
    Standard serializer for individual RoomImage operations.
    """
    class Meta:
        model = RoomImage
        fields = ["id", "room", "image", "caption", "is_cover", "order", "is_active", "created_at"]


class RoomFacilityReadSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for room-facility relationships.
    """
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
    Production-standard write serializer for Rooms.
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

    def validate_capacity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Capacity must be greater than zero.")
        return value

    def validate(self, data):
        """
        Check that room_number is unique within the hostel.
        """
        hostel = data.get("hostel")
        room_number = data.get("room_number")
        
        # In case of update, instance is available
        instance = self.instance
        
        queryset = Room.objects.filter(hostel=hostel, room_number=room_number)
        if instance:
            queryset = queryset.exclude(pk=instance.pk)
            
        if queryset.exists():
            raise serializers.ValidationError({
                "room_number": f"Room number '{room_number}' already exists for this hostel."
            })
            
        return data

    @transaction.atomic
    def create(self, validated_data):
        facility_ids = validated_data.pop("facility_ids", [])
        uploaded_images = validated_data.pop("uploaded_images", [])
        
        room = Room.objects.create(**validated_data)

        # Bulk create relationship entries for performance
        if facility_ids:
            room_facilities = [
                RoomFacility(room=room, facility_id=fid)
                for fid in facility_ids
            ]
            RoomFacility.objects.bulk_create(room_facilities)

        # Handle image uploads
        if uploaded_images:
            room_images = [
                RoomImage(room=room, image=img)
                for img in uploaded_images
            ]
            RoomImage.objects.bulk_create(room_images)

        return room

    @transaction.atomic
    def update(self, instance, validated_data):
        facility_ids = validated_data.pop("facility_ids", None)
        uploaded_images = validated_data.pop("uploaded_images", None)

        # Update base fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update Facilities (Sync logic)
        if facility_ids is not None:
            # Simple replace logic for facilities
            instance.room_facilities.all().delete()
            room_facilities = [
                RoomFacility(room=instance, facility_id=fid)
                for fid in facility_ids
            ]
            RoomFacility.objects.bulk_create(room_facilities)

        # Append new images (standard behavior for multiple uploads)
        if uploaded_images:
            room_images = [
                RoomImage(room=instance, image=img)
                for img in uploaded_images
            ]
            RoomImage.objects.bulk_create(room_images)

        return instance
