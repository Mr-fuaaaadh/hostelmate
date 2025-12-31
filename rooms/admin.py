from django.contrib import admin
from django import forms
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import Room, Facility, RoomFacility, RoomImage

# =====================================================
# Facility Admin
# =====================================================
@admin.register(Facility)
class FacilityAdmin(ImportExportModelAdmin):
    list_display = ("name", "slug", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


# =====================================================
# RoomImage Inline for Room Admin
# =====================================================
class RoomImageInline(admin.TabularInline):
    model = RoomImage
    extra = 1
    fields = ("image_preview", "image", "caption", "is_cover", "order", "is_active")
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height: 80px;" />', obj.image.url)
        return "-"
    image_preview.short_description = "Preview"


# =====================================================
# RoomFacility Inline for Room Admin
# =====================================================
class RoomFacilityInline(admin.TabularInline):
    model = RoomFacility
    extra = 1
    autocomplete_fields = ["facility"]


# =====================================================
# Room Resource for bulk import/export
# =====================================================
class RoomResource(resources.ModelResource):
    class Meta:
        model = Room
        fields = ("id", "hostel", "room_number", "room_type", "capacity", "daily_price", "monthly_price", "is_available")


# =====================================================
# Room Admin
# =====================================================
@admin.register(Room)
class RoomAdmin(ImportExportModelAdmin):
    resource_class = RoomResource
    list_display = ("room_number", "hostel", "room_type", "capacity", "is_available", "daily_price", "monthly_price")
    list_filter = ("room_type", "is_available", "hostel")
    search_fields = ("room_number", "hostel__name")
    ordering = ("hostel", "room_number")
    inlines = [RoomFacilityInline, RoomImageInline]


# =====================================================
# RoomFacility Admin
# =====================================================
@admin.register(RoomFacility)
class RoomFacilityAdmin(admin.ModelAdmin):
    list_display = ("room", "facility")
    list_filter = ("facility",)
    search_fields = ("room__room_number", "facility__name")
    autocomplete_fields = ["room", "facility"]


# =====================================================
# RoomImage Admin
# =====================================================
@admin.register(RoomImage)
class RoomImageAdmin(admin.ModelAdmin):
    list_display = ("room", "image_preview", "caption", "is_cover", "order", "is_active", "created_at")
    list_filter = ("is_cover", "is_active", "room__hostel")
    search_fields = ("room__room_number", "caption", "room__hostel__name")
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height: 80px;" />', obj.image.url)
        return "-"
    image_preview.short_description = "Preview"
