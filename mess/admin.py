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


admin.site.register(Home)
admin.site.register(HomeImage)
admin.site.register(DeliveryArea)
admin.site.register(MealPlan)
admin.site.register(ProviderFeature)

