from rest_framework import serializers
from .models import Room, Facility, RoomImage, RoomFacility

# Facility Serializer
class FacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Facility
        fields = ["id", "name", "slug"]

# Room Facility Serializer
class RoomFacilitySerializer(serializers.ModelSerializer):
    facility = FacilitySerializer(read_only=True)
    facility_id = serializers.PrimaryKeyRelatedField(
        queryset=Facility.objects.all(),
        source="facility",
        write_only=True
    )

    class Meta:
        model = RoomFacility
        fields = ["id", "facility", "facility_id"]

# Room Image Serializer
class RoomImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomImage
        fields = ["id","room", "image", "caption", "is_cover", "order", "is_active"]

# Room Serializer (Full)
class RoomSerializer(serializers.ModelSerializer):
    images = RoomImageSerializer(many=True, read_only=True)
    room_facilities = RoomFacilitySerializer(many=True, read_only=True)
    hostel_name = serializers.CharField(source="hostel.name", read_only=True)

    class Meta:
        model = Room
        fields = [
            "id", "hostel", "hostel_name", "room_number", "room_type",
            "is_available", "capacity", "daily_price", "monthly_price",
            "description", "images", "room_facilities"
        ]

# Room Create/Update Serializer
class RoomCreateUpdateSerializer(serializers.ModelSerializer):
    room_facilities = RoomFacilitySerializer(many=True, required=False)
    images = RoomImageSerializer(many=True, required=False)

    class Meta:
        model = Room
        fields = [
            "hostel", "room_number", "room_type", "is_available",
            "capacity", "daily_price", "monthly_price", "description",
            "room_facilities", "images"
        ]

    def create(self, validated_data):
        facilities_data = validated_data.pop("room_facilities", [])
        images_data = validated_data.pop("images", [])
        room = Room.objects.create(**validated_data)

        for fdata in facilities_data:
            RoomFacility.objects.create(room=room, **fdata)
        for idata in images_data:
            RoomImage.objects.create(room=room, **idata)

        return room

    def update(self, instance, validated_data):
        facilities_data = validated_data.pop("room_facilities", [])
        images_data = validated_data.pop("images", [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if facilities_data:
            instance.room_facilities.all().delete()
            for fdata in facilities_data:
                RoomFacility.objects.create(room=instance, **fdata)

        if images_data:
            instance.images.all().delete()
            for idata in images_data:
                RoomImage.objects.create(room=instance, **idata)

        return instance
