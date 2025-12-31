from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin

from .models import CustomUser
from .resources import CustomUserResource


@admin.register(CustomUser)
class CustomUserAdmin(ImportExportModelAdmin, BaseUserAdmin):
    resource_class = CustomUserResource
    model = CustomUser

    # -----------------------
    # List view
    # -----------------------
    list_display = (
        "email",
        "full_name",
        "role",
        "phone_number",
        "email_verified",
        "phone_verified",
        "kyc_verified",
        "is_active",
        "is_deleted",
        "registered_at",
        "profile_image_preview",
    )

    list_filter = (
        "role",
        "is_active",
        "is_deleted",
        "email_verified",
        "phone_verified",
        "kyc_verified",
        "city",
        "state",
    )

    search_fields = (
        "email",
        "first_name",
        "last_name",
        "phone_number",
    )

    ordering = ("-registered_at",)
    readonly_fields = ("registered_at", "last_active", "profile_image_preview")

    # -----------------------
    # Form layout
    # -----------------------
    fieldsets = (
        ("Account", {"fields": ("email", "password", "role")}),
        ("Personal Info", {
            "fields": (
                "first_name",
                "last_name",
                "phone_number",
                "profile_image",
                "profile_image_preview",
                "gender",
                "date_of_birth",
                "bio",
            )
        }),
        ("Address", {"fields": ("address", "city", "state", "country", "postal_code")}),
        ("Verification", {"fields": ("email_verified", "phone_verified", "kyc_verified")}),
        ("Status", {"fields": ("is_active", "is_deleted")}),
        ("Activity", {"fields": ("last_login_ip", "last_active", "registered_at")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "password1",
                "password2",
                "role",
                "first_name",
                "last_name",
                "phone_number",
                "email_verified",
                "phone_verified",
                "kyc_verified",
            ),
        }),
    )

    # -----------------------
    # Helpers
    # -----------------------
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
    full_name.short_description = "Full Name"

    def profile_image_preview(self, obj):
        if obj.profile_image:
            return format_html(
                '<img src="{}" style="width:40px;height:40px;border-radius:50%;" />',
                obj.profile_image.url,
            )
        return "-"
    profile_image_preview.short_description = "Profile Image"

    # -----------------------
    # Bulk Actions
    # -----------------------
    actions = (
        "bulk_activate",
        "bulk_deactivate",
        "bulk_verify_email",
        "bulk_verify_phone",
        "bulk_verify_kyc",
        "bulk_soft_delete",
        "bulk_restore",
    )

    def bulk_activate(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count} users activated")
    bulk_activate.short_description = "Activate selected users"

    def bulk_deactivate(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} users deactivated")
    bulk_deactivate.short_description = "Deactivate selected users"

    def bulk_verify_email(self, request, queryset):
        count = queryset.update(email_verified=True)
        self.message_user(request, f"{count} emails verified")
    bulk_verify_email.short_description = "Verify email"

    def bulk_verify_phone(self, request, queryset):
        count = queryset.update(phone_verified=True)
        self.message_user(request, f"{count} phone numbers verified")
    bulk_verify_phone.short_description = "Verify phone"

    def bulk_verify_kyc(self, request, queryset):
        count = queryset.update(kyc_verified=True)
        self.message_user(request, f"{count} users KYC verified")
    bulk_verify_kyc.short_description = "Verify KYC"

    def bulk_soft_delete(self, request, queryset):
        count = queryset.update(is_deleted=True, is_active=False)
        self.message_user(request, f"{count} users soft deleted")
    bulk_soft_delete.short_description = "Soft delete users"

    def bulk_restore(self, request, queryset):
        count = queryset.update(is_deleted=False, is_active=True)
        self.message_user(request, f"{count} users restored")
    bulk_restore.short_description = "Restore users"
