from import_export import resources, fields
from import_export.widgets import BooleanWidget
from .models import CustomUser


class CustomUserResource(resources.ModelResource):
    email_verified = fields.Field(
        column_name="email_verified",
        attribute="email_verified",
        widget=BooleanWidget(),
    )
    phone_verified = fields.Field(
        column_name="phone_verified",
        attribute="phone_verified",
        widget=BooleanWidget(),
    )
    kyc_verified = fields.Field(
        column_name="kyc_verified",
        attribute="kyc_verified",
        widget=BooleanWidget(),
    )

    class Meta:
        model = CustomUser
        import_id_fields = ("email",)   # ✅ Prevent duplicates
        skip_unchanged = True
        report_skipped = True

        fields = (
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "role",
            "is_active",
            "is_deleted",
            "email_verified",
            "phone_verified",
            "kyc_verified",
            "city",
            "state",
            "country",
        )




