from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from users.models import CustomUser



class Home(models.Model):
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="homes")
    name = models.CharField(max_length=200, db_index=True)
    cover_image = models.URLField(blank=True, null=True)
    address = models.TextField()
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100, db_index=True)
    pincode = models.CharField(max_length=10)
    description = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False, db_index=True)
    mess_menus = GenericRelation("MessMenu", related_query_name="home")

    class Meta:
        verbose_name = _("Home")
        verbose_name_plural = _("Homes")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["city", "state"]),
            models.Index(fields=["owner", "is_verified"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.city})"


class HomeImage(models.Model):
    home = models.ForeignKey(Home, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="home/", max_length=1000)
    alt_text = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Home Image")
        verbose_name_plural = _("Home Images")

    def __str__(self):
        return f"{self.alt_text or 'Image'} ({self.home.name})"


class MessMenu(models.Model):
    DAY_CHOICES = [
        ("Monday", "Monday"),
        ("Tuesday", "Tuesday"),
        ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"),
        ("Friday", "Friday"),
        ("Saturday", "Saturday"),
        ("Sunday", "Sunday"),
    ]

    # Generic Foreign Key
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    provider = GenericForeignKey("content_type", "object_id")

    day = models.CharField(max_length=10, choices=DAY_CHOICES, db_index=True)

    # Veg meals
    veg_breakfast = models.CharField(max_length=150, blank=True, null=True)
    veg_breakfast_accompaniment = models.CharField(max_length=150, blank=True, null=True)
    veg_lunch = models.CharField(max_length=150, blank=True, null=True)
    veg_lunch_accompaniment = models.CharField(max_length=150, blank=True, null=True)
    veg_dinner = models.CharField(max_length=150, blank=True, null=True)
    veg_dinner_accompaniment = models.CharField(max_length=150, blank=True, null=True)

    # Non-veg meals
    nonveg_breakfast = models.CharField(max_length=150, blank=True, null=True)
    nonveg_breakfast_accompaniment = models.CharField(max_length=150, blank=True, null=True)
    nonveg_lunch = models.CharField(max_length=150, blank=True, null=True)
    nonveg_lunch_accompaniment = models.CharField(max_length=150, blank=True, null=True)
    nonveg_dinner = models.CharField(max_length=150, blank=True, null=True)
    nonveg_dinner_accompaniment = models.CharField(max_length=150, blank=True, null=True)

    # Meal images
    breakfast_image = models.ImageField(upload_to="mess_menu/breakfast/", blank=True, null=True)
    lunch_image = models.ImageField(upload_to="mess_menu/lunch/", blank=True, null=True)
    dinner_image = models.ImageField(upload_to="mess_menu/dinner/", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("content_type", "object_id", "day")
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["day"]),
        ]
        ordering = ["day"]

    def __str__(self):
        return f"{self.provider} - {self.day}"
    



class DeliveryArea(models.Model):
    provider_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    provider_id = models.PositiveIntegerField()
    provider = GenericForeignKey("provider_type", "provider_id")

    area_name = models.CharField(max_length=100, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Delivery Area")
        verbose_name_plural = _("Delivery Areas")
        ordering = ["area_name"]

    def __str__(self):
        return f"{self.area_name} ({self.provider})"



class MealPlan(models.Model):
    provider_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    provider_id = models.PositiveIntegerField()
    provider = GenericForeignKey("provider_type", "provider_id")

    plan_id = models.CharField(max_length=50, db_index=True)
    name = models.CharField(max_length=100, db_index=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    meals = models.PositiveIntegerField(blank=True, null=True)
    features = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Meal Plan")
        verbose_name_plural = _("Meal Plans")
        ordering = ["name"]
        indexes = [
            models.Index(fields=["provider_type", "provider_id"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.provider})"



class ProviderFeature(models.Model):
    provider_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    provider_id = models.PositiveIntegerField()
    provider = GenericForeignKey("provider_type", "provider_id")

    icon = models.CharField(max_length=50, blank=True)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Provider Feature")
        verbose_name_plural = _("Provider Features")
        ordering = ["title"]

    def __str__(self):
        return f"{self.title} ({self.provider})"
