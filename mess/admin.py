from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources

from .models import (
    Home,
    HomeImage,
    MessMenu,
    DeliveryArea,
    MealPlan,
    ProviderFeature
)


class MessMenuResource(resources.ModelResource):
    class Meta:
        model = MessMenu

        # Fields allowed for import/export
        fields = (
            "content_type",
            "object_id",
            "day",

            "veg_breakfast",
            "veg_breakfast_accompaniment",
            "veg_lunch",
            "veg_lunch_accompaniment",
            "veg_dinner",
            "veg_dinner_accompaniment",

            "nonveg_breakfast",
            "nonveg_breakfast_accompaniment",
            "nonveg_lunch",
            "nonveg_lunch_accompaniment",
            "nonveg_dinner",
            "nonveg_dinner_accompaniment",
        )

        # Prevent duplicates
        import_id_fields = ("content_type", "object_id", "day")

        skip_unchanged = True
        report_skipped = True



@admin.register(MessMenu)
class MessMenuAdmin(ImportExportModelAdmin):
    resource_class = MessMenuResource   # 🔥 THIS LINE FIXES YOUR ERROR

    list_display = (
        "day",
        "veg_breakfast",
        "veg_lunch",
        "veg_dinner",
        "nonveg_lunch",
    )

    list_filter = ("day",)

    search_fields = (
        "veg_breakfast",
        "veg_lunch",
        "veg_dinner",
        "nonveg_lunch",
    )

    ordering = ("day",)


@admin.register(Home)
class HomeAdmin(ImportExportModelAdmin):
    list_display = ("name", "city", "state", "owner", "is_verified", "created_at")
    search_fields = ("name", "city", "state", "pincode")
    list_filter = ("city", "state", "is_verified")



@admin.register(HomeImage)
class HomeImageAdmin(ImportExportModelAdmin):
    list_display = ("id", "home", "image", "alt_text", "created_at")
    search_fields = ("home__name", "image", "alt_text")
    list_filter = ("home",)
    readonly_fields = ("created_at",)


@admin.register(DeliveryArea)
class DeliveryAreaAdmin(ImportExportModelAdmin):
    list_display = ("id", "area_name", "provider", "created_at")
    search_fields = ("area_name", "provider__id")
    list_filter = ("provider_type",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(MealPlan)
class MealPlanAdmin(ImportExportModelAdmin):
    list_display = ("plan_id", "name", "price", "meals")
    search_fields = ("plan_id", "name")


@admin.register(ProviderFeature)
class ProviderFeatureAdmin(ImportExportModelAdmin):
    list_display = ("id", "title", "provider", "created_at")
    search_fields = ("title", "description", "provider__id")