from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import Hostel, HostelImage, HostelRule, Facility
from rooms.models import Room
import logging

logger = logging.getLogger(__name__)

# Update hostel room counts
@receiver([post_save, post_delete], sender=Room)
def update_hostel_room_counts(sender, instance, **kwargs):
    hostel = instance.hostel
    hostel.total_rooms_count = hostel.rooms.count()
    hostel.available_rooms_count = hostel.rooms.filter(is_available=True).count()
    hostel.save(update_fields=['total_rooms_count', 'available_rooms_count'])
    logger.info(f"Updated room counts for hostel {hostel.name}")

# Enforce single cover image
@receiver(pre_save, sender=HostelImage)
def enforce_single_cover_image(sender, instance, **kwargs):
    if instance.is_cover:
        HostelImage.objects.filter(hostel=instance.hostel, is_cover=True).exclude(pk=instance.pk).update(is_cover=False)

# Cleanup image files
@receiver(post_delete, sender=HostelImage)
def cleanup_image(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)
    logger.info(f"Deleted image for hostel: {instance.hostel.name}")

# Log rule deletion
@receiver(post_delete, sender=HostelRule)
def cleanup_rule(sender, instance, **kwargs):
    logger.info(f"Rule deleted: {instance.title} ({instance.hostel.name})")
