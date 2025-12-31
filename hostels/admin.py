from django.contrib import admin
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import Hostel, HostelImage, HostelFacility, HostelRule
from rooms.models import Facility
from users.resources import CustomUserResource

# =====================================================
# Hostel Facility Inline
# =====================================================
class HostelFacilityInline(admin.TabularInline):
    model = HostelFacility
    extra = 1
    autocomplete_fields = ["facility"]


# =====================================================
# Hostel Image Inline
# =====================================================
class HostelImageInline(admin.TabularInline):
    model = HostelImage
    extra = 1
    fields = ("image_preview", "image", "caption", "is_cover", "order", "is_active")
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:80px;" />', obj.image.url)
        return "-"
    image_preview.short_description = "Preview"


# =====================================================
# Hostel Rule Inline
# =====================================================
class HostelRuleInline(admin.TabularInline):
    model = HostelRule
    extra = 1
    fields = ("title", "description", "rule_type", "is_active")


# =====================================================
# Hostel Resource for Import/Export
# =====================================================
class HostelResource(resources.ModelResource):
    class Meta:
        model = Hostel
        fields = (
            "id", "owner", "name", "description", "address", "city", "state",
            "pincode", "hostel_type", "latitude", "longitude",
            "is_verified", "is_active", "available_rooms_count", "total_rooms_count",
        )


# =====================================================
# Hostel Admin
# =====================================================
@admin.register(Hostel)
class HostelAdmin(ImportExportModelAdmin):
    resource_class = HostelResource
    list_display = ("name", "owner", "city", "state", "hostel_type", "is_verified", "is_active", "available_rooms_count", "total_rooms_count")
    list_filter = ("hostel_type", "is_verified", "is_active", "city", "state")
    search_fields = ("name", "city", "state", "address", "owner__email")
    ordering = ("-created_at",)
    inlines = [HostelFacilityInline, HostelImageInline, HostelRuleInline]
    autocomplete_fields = ["owner"]


# =====================================================
# Hostel Facility Admin
# =====================================================
@admin.register(HostelFacility)
class HostelFacilityAdmin(admin.ModelAdmin):
    list_display = ("hostel", "facility")
    search_fields = ("hostel__name", "facility__name")
    autocomplete_fields = ["hostel", "facility"]


# =====================================================
# Hostel Image Admin
# =====================================================
@admin.register(HostelImage)
class HostelImageAdmin(admin.ModelAdmin):
    list_display = ("hostel", "image_preview", "caption", "is_cover", "order", "is_active", "created_at")
    list_filter = ("is_cover", "is_active", "hostel")
    search_fields = ("hostel__name", "caption")
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:80px;" />', obj.image.url)
        return "-"
    image_preview.short_description = "Preview"


# =====================================================
# Hostel Rule Admin
# =====================================================
@admin.register(HostelRule)
class HostelRuleAdmin(admin.ModelAdmin):
    list_display = ("title", "hostel", "rule_type", "is_active")
    list_filter = ("rule_type", "is_active", "hostel")
    search_fields = ("title", "hostel__name")




