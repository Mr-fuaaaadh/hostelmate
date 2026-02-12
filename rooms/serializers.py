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
    Supports selective deletion of images and facilities during update.
    """
    facility = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of Facility IDs to add"
    )
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
        help_text="Multiple binary image files to upload"
    )
    deleted_images = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    deleted_facilities = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of Facility IDs to remove"
    )

    class Meta:
        model = Room
        fields = [
            "hostel", "room_number", "room_type", "is_available",
            "capacity", "daily_price", "monthly_price", "description",
            "facility", "images", "deleted_images", "deleted_facilities"
        ]

    def to_internal_value(self, data):
        """
        Handle both JSON (dict) and Form (QueryDict) data.
        Ensures multi-value fields are correctly extracted and filters out 
        empty values that cause validation errors in integer fields.
        """
        is_querydict = hasattr(data, 'getlist')
        
        # Create a mutable copy without triggering deepcopy on files
        if is_querydict:
            processed_data = data.dict()
        else:
            processed_data = data.copy() if hasattr(data, 'copy') else dict(data)

        # Fields that must be handled as lists
        list_fields = ["facility", "images", "deleted_images", "deleted_facilities"]

        for field_name in list_fields:
            if field_name in data:
                # Get the raw value correctly based on input type
                raw_value = data.getlist(field_name) if is_querydict else data[field_name]
                
                # Normalize raw_value to a list of strings/objects
                if isinstance(raw_value, str) and "," in raw_value:
                    processed_data[field_name] = [v.strip() for v in raw_value.split(",") if v.strip()]
                elif isinstance(raw_value, list) and len(raw_value) == 1 and isinstance(raw_value[0], str) and "," in raw_value[0]:
                    processed_data[field_name] = [v.strip() for v in raw_value[0].split(",") if v.strip()]
                elif isinstance(raw_value, list):
                    # Filter out empty strings and None which cause IntegerField validation errors
                    processed_data[field_name] = [v for v in raw_value if v not in ["", None]]
                elif raw_value not in ["", None]:
                    processed_data[field_name] = [raw_value]
                else:
                    processed_data[field_name] = []
        
        return super().to_internal_value(processed_data)

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
        
        if hostel and room_number:
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
        facility = validated_data.pop("facility", [])
        images = validated_data.pop("images", [])
        
        # RoomWriteSerializer doesn't expect deleted_ fields in create, but we pop them to be safe
        validated_data.pop("deleted_images", None)
        validated_data.pop("deleted_facilities", None)
        
        room = Room.objects.create(**validated_data)

        # Bulk create relationship entries
        if facility:
            room_facilities = [
                RoomFacility(room=room, facility_id=fid)
                for fid in facility
            ]
            RoomFacility.objects.bulk_create(room_facilities)

        # Handle image uploads
        if images:
            room_images = [
                RoomImage(room=room, image=img)
                for img in images
            ]
            RoomImage.objects.bulk_create(room_images)

        return room

    @transaction.atomic
    def update(self, instance, validated_data):
        facility_ids = validated_data.pop("facility", None)
        images = validated_data.pop("images", None)
        deleted_images = validated_data.pop("deleted_images", [])
        deleted_facilities = validated_data.pop("deleted_facilities", [])

        # Update base fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Handle Selective Deletions
        if deleted_images:
            deleted_count, _ = RoomImage.objects.filter(
                id__in=deleted_images,
                room=instance
            ).delete()

        if deleted_facilities:
            deleted_count, _ = RoomFacility.objects.filter(
                facility_id__in=deleted_facilities, 
                room=instance
            ).delete()

        # Add new Facilities (Avoid duplicates)
        if facility_ids is not None:
            existing_fids = set(instance.room_facilities.values_list('facility_id', flat=True))
            new_fids = [fid for fid in facility_ids if fid not in existing_fids]
            
            if new_fids:
                room_facilities = [
                    RoomFacility(room=instance, facility_id=fid)
                    for fid in new_fids
                ]
                RoomFacility.objects.bulk_create(room_facilities)

        # Append new images
        if images:
            room_images = [
                RoomImage(room=instance, image=img)
                for img in images
            ]
            RoomImage.objects.bulk_create(room_images)

        return instance

    def to_representation(self, instance):
        return RoomReadSerializer(instance, context=self.context).data
