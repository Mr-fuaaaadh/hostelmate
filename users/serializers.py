from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from hostels.models import Hostel
from mess.models import MessMenu
from hostels.serializers import HostelImageSerializer, HostelFacilitySerializer
from rooms.serializers import RoomReadSerializer
from mess.serializers import MessMenuSerializer

User = get_user_model()


# ---------------------------------------------------------------------
# User Registration Serializer
# ---------------------------------------------------------------------
class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for new user registration with password validation and 
    role-based requirements.
    """
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
        """
        Custom validation for password matching and role-specific requirements.
        """
        if data["password"] != data["password2"]:
            raise serializers.ValidationError(
                {"password": "Passwords do not match"}
            )

        # Enforce phone_number for owners
        role = data.get("role")
        phone = data.get("phone_number")
        if role in [User.Roles.OWNER, User.Roles.MESS_OWNER] and not phone:
            raise serializers.ValidationError(
                {"phone_number": "Phone number is required for hostel or mess owners."}
            )

        return data

    def create(self, validated_data):
        """
        Creates a new user using the custom manager.
        """
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
    """
    Serializer for retrieving and updating the authenticated user's profile.
    Sensitive fields are read-only.
    """
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


# ---------------------------------------------------
# User-Side Detail Serializers (Optimized for Read)
# ---------------------------------------------------

class UserHostelDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for hostels from a user perspective, 
    including images, facilities, rooms, and mess menus.
    """
    images = HostelImageSerializer(many=True, read_only=True)
    hostel_facilities = HostelFacilitySerializer(many=True, read_only=True)
    rooms = RoomReadSerializer(many=True, read_only=True)
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
        """
        Retrieves the mess menu associated with the hostel.
        """
        content_type = ContentType.objects.get_for_model(Hostel)
        menus = MessMenu.objects.filter(
            content_type=content_type,
            object_id=obj.id
        ).order_by("id")

        return MessMenuSerializer(menus, many=True).data

