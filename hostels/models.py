from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericRelation
from users.models import CustomUser
from rooms.models import Facility


class MessProviderMixin(models.Model):
    mess_menus = GenericRelation(
        "mess.MessMenu",
        content_type_field="content_type",
        object_id_field="object_id",
        related_query_name="provider"
    )

    meal_plans = GenericRelation(
        "mess.MealPlan",
        content_type_field="provider_type",
        object_id_field="provider_id",
        related_query_name="provider"
    )

    delivery_areas = GenericRelation(
        "mess.DeliveryArea",
        content_type_field="provider_type",
        object_id_field="provider_id",
        related_query_name="provider"
    )

    features = GenericRelation(
        "mess.ProviderFeature",
        content_type_field="provider_type",
        object_id_field="provider_id",
        related_query_name="provider"
    )

    class Meta:
        abstract = True



class Hostel(MessProviderMixin, models.Model):
    class HostelType(models.TextChoices):
        GENTS = "gents", _("Gents")
        LADIES = "ladies", _("Ladies")
        MIXED = "mixed", _("Mixed")

    owner = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="hostels",
        db_index=True
    )

    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField(blank=True)
    address = models.TextField()

    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100, db_index=True)
    pincode = models.CharField(max_length=10, db_index=True)

    hostel_type = models.CharField(
        max_length=10,
        choices=HostelType.choices,
        default=HostelType.MIXED,
        db_index=True
    )

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    is_verified = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True)

    available_rooms_count = models.PositiveIntegerField(default=0, db_index=True)
    total_rooms_count = models.PositiveIntegerField(default=0, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["city", "state"]),
            models.Index(fields=["hostel_type"]),
            models.Index(fields=["owner", "is_verified"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.city})"


    @property
    def availability_summary(self):
        return f"{self.available_rooms_count}/{self.total_rooms_count} rooms available"


class HostelFacility(models.Model):
    hostel = models.ForeignKey(
        Hostel,
        on_delete=models.CASCADE,
        related_name="hostel_facilities"
    )
    facility = models.ForeignKey(
        Facility,
        on_delete=models.CASCADE,
        related_name="hostel_facilities"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["hostel", "facility"],
                name="unique_hostel_facility"
            )
        ]
        verbose_name = _("Hostel Facility")
        verbose_name_plural = _("Hostel Facilities")

    def __str__(self):
        return f"{self.hostel.name} - {self.facility.name}"



def hostel_image_upload_path(instance, filename):
    return f"hostels/{instance.hostel.id}/images/{filename}"


class HostelImage(models.Model):
    hostel = models.ForeignKey(Hostel,on_delete=models.CASCADE,related_name="images")
    image = models.ImageField(upload_to=hostel_image_upload_path)
    caption = models.CharField(max_length=255,blank=True)
    is_cover = models.BooleanField(default=False,help_text="Primary image for hostel listing")
    order = models.PositiveIntegerField(default=0,help_text="Image display order")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "-created_at"]
        verbose_name = _("Hostel Image")
        verbose_name_plural = _("Hostel Images")
        indexes = [
            models.Index(fields=["hostel", "is_cover"]),
        ]

    def save(self, *args, **kwargs):
        # Ensure only one cover image per hostel
        if self.is_cover:
            HostelImage.objects.filter(
                hostel=self.hostel,
                is_cover=True
            ).exclude(pk=self.pk).update(is_cover=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.hostel.name} - Image {self.id}"
    


class HostelRule(models.Model):
    class RuleType(models.TextChoices):
        GENERAL = "general", _("General")
        SAFETY = "safety", _("Safety")
        TIMINGS = "timings", _("Timings")
        BEHAVIOR = "behavior", _("Behavior")

    hostel = models.ForeignKey(
        Hostel,
        on_delete=models.CASCADE,
        related_name="rules",
        db_index=True
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    rule_type = models.CharField(
        max_length=20,
        choices=RuleType.choices,
        default=RuleType.GENERAL,
        db_index=True
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Deactivated rules won't be shown to users"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Hostel Rule")
        verbose_name_plural = _("Hostel Rules")
        ordering = ["hostel", "rule_type", "title"]
        indexes = [
            models.Index(fields=["hostel", "rule_type"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.hostel.name})"