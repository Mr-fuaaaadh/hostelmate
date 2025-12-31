from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from hostels.models import Hostel, HostelImage, HostelFacility
from rooms.models import Room, RoomImage, RoomFacility
from mess.models import MessMenu
User = get_user_model()


# ---------------------------------------------------------------------
# User Registration Serializer
# ---------------------------------------------------------------------
class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "password2",
            "role",
            "first_name",
            "last_name",
            "phone_number",
            "profile_image",
        ]
        extra_kwargs = {
            "email": {"required": True},
        }

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError(
                {"password": "Passwords do not match"}
            )

        # Optional: enforce phone_number for owners
        role = data.get("role")
        phone = data.get("phone_number")
        if role in [User.Roles.OWNER, User.Roles.MESS_OWNER] and not phone:
            raise serializers.ValidationError(
                {"phone_number": "Phone number is required for owners"}
            )

        return data

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")

        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        return user


# ---------------------------------------------------
# Profile Serializer
# ---------------------------------------------------
class LoggedUserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "role",
            "profile_image",
            "bio",
            "gender",
            "date_of_birth",
            "address",
            "city",
            "state",
            "country",
            "postal_code",
            "email_verified",
            "phone_verified",
            "kyc_verified",
            "is_active",
            "registered_at",
        ]
        read_only_fields = [
            "id",
            "email",
            "role",
            "email_verified",
            "phone_verified",
            "kyc_verified",
            "registered_at",
        ]




class RoomImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomImage
        fields = ["id", "image", "caption", "is_cover"]

class RoomFacilitySerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(source='facility.name', read_only=True)
    class Meta:
        model = RoomFacility
        fields = ["id", "facility_name"]

class RoomSerializer(serializers.ModelSerializer):
    images = RoomImageSerializer(many=True, read_only=True)
    room_facilities = RoomFacilitySerializer(many=True, read_only=True)

    class Meta:
        model = Room
        fields = [
            "id", "room_number", "room_type", "capacity",
            "daily_price", "monthly_price", "is_available",
            "images", "room_facilities"
        ]

class HostelFacilitySerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(source='facility.name', read_only=True)
    class Meta:
        model = HostelFacility
        fields = ["id","facility_name"]

class HostelImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = HostelImage
        fields = ["id", "image", "caption", "is_cover"]

class MessMenuSerializer(serializers.ModelSerializer):
    # Grouping veg and non-veg meals separately
    veg = serializers.SerializerMethodField()
    nonveg = serializers.SerializerMethodField()

    class Meta:
        model = MessMenu
        fields = [
            "id",
            "day",
            "veg",
            "nonveg",
        ]

    def get_veg(self, obj):
        return {
            "breakfast": obj.veg_breakfast,
            "breakfast_accompaniment": obj.veg_breakfast_accompaniment,
            "lunch": obj.veg_lunch,
            "lunch_accompaniment": obj.veg_lunch_accompaniment,
            "dinner": obj.veg_dinner,
            "dinner_accompaniment": obj.veg_dinner_accompaniment,
        }

    def get_nonveg(self, obj):
        return {
            "breakfast": obj.nonveg_breakfast,
            "breakfast_accompaniment": obj.nonveg_breakfast_accompaniment,
            "lunch": obj.nonveg_lunch,
            "lunch_accompaniment": obj.nonveg_lunch_accompaniment,
            "dinner": obj.nonveg_dinner,
            "dinner_accompaniment": obj.nonveg_dinner_accompaniment,
        }


class UserHostelDetailSerializer(serializers.ModelSerializer):
    images = HostelImageSerializer(many=True, read_only=True)
    hostel_facilities = HostelFacilitySerializer(many=True, read_only=True)
    rooms = RoomSerializer(many=True, read_only=True)
    availability_summary = serializers.CharField(read_only=True)

    mess_menu = serializers.SerializerMethodField()

    class Meta:
        model = Hostel
        fields = [
            "id", "name", "description", "address", "city", "state", "pincode",
            "hostel_type", "latitude", "longitude",
            "available_rooms_count", "total_rooms_count",
            "availability_summary",

            "images",
            "hostel_facilities",
            "rooms",

            "mess_menu"
        ]

    def get_mess_menu(self, obj):
        content_type = ContentType.objects.get_for_model(Hostel)
        menus = MessMenu.objects.filter(
            content_type=content_type,
            object_id=obj.id
        ).order_by("id")

        return MessMenuSerializer(menus, many=True).data

