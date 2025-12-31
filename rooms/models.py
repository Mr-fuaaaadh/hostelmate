from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify

class Room(models.Model):
    class RoomType(models.TextChoices):
        SINGLE = "single", _("Single")
        DOUBLE = "double", _("Double")
        TRIPLE = "triple", _("Triple")
        DORM = "dorm", _("Dormitory")

    hostel = models.ForeignKey("hostels.Hostel", on_delete=models.CASCADE, related_name="rooms")
    room_number = models.CharField(max_length=50)
    room_type = models.CharField(max_length=10, choices=RoomType.choices)
    is_available = models.BooleanField(default=True)
    capacity = models.PositiveIntegerField()
    daily_price = models.DecimalField(max_digits=10, decimal_places=2)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ("hostel", "room_number")
        ordering = ["room_number"]

    def __str__(self):
        return f"{self.hostel.name} - Room {self.room_number} ({self.room_type})"
    

class Facility(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("Facility")
        verbose_name_plural = _("Facilities")

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            i = 1
            while Facility.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name



class RoomFacility(models.Model):
    room = models.ForeignKey("rooms.Room", on_delete=models.CASCADE, related_name="room_facilities")
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name="room_facilities")

    class Meta:
        verbose_name = _("Room Facility")
        verbose_name_plural = _("Room Facilities")
        unique_together = ("room", "facility")

    def __str__(self):
        return f"{self.facility.name} ({self.room.hostel.name} - Room {self.room.room_number})"
    


def room_image_upload_path(instance, filename):
    return f"hostels/{instance.room.hostel.id}/rooms/{instance.room.id}/{filename}"


class RoomImage(models.Model):
    room = models.ForeignKey("rooms.Room",on_delete=models.CASCADE,related_name="images")
    image = models.ImageField(upload_to=room_image_upload_path)
    caption = models.CharField(max_length=255,blank=True)
    is_cover = models.BooleanField(default=False,help_text="Primary image for this room")
    order = models.PositiveIntegerField(default=0,help_text="Image display order")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["order", "-created_at"]
        verbose_name = _("Room Image")
        verbose_name_plural = _("Room Images")
        indexes = [
            models.Index(fields=["room", "is_cover"]),
        ]

    def save(self, *args, **kwargs):
        # Ensure only one cover image per room
        if self.is_cover:
            RoomImage.objects.filter(
                room=self.room,
                is_cover=True
            ).exclude(pk=self.pk).update(is_cover=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.room.hostel.name} - Room {self.room.room_number} - Image {self.id}"