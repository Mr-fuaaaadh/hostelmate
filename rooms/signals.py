from django.db import models
from django.db.models.signals import pre_save, post_delete, post_save
from django.dispatch import receiver
from .models import Room, RoomImage
import logging

logger = logging.getLogger(__name__)

# --------------------------------------------------
# Update hostel room counts when room changes
# --------------------------------------------------
@receiver([post_save, post_delete], sender=Room)
def update_hostel_room_counts(sender, instance, **kwargs):
    """
    Automatically updates the total and available room counts for a hostel 
    whenever a room is created, updated, or deleted.
    """
    if not instance.hostel_id:
        return

    try:
        hostel = instance.hostel
        
        # Use aggregate for better performance if counts are complex
        counts = hostel.rooms.aggregate(
            total=models.Count('id'),
            available=models.Count('id', filter=models.Q(is_available=True))
        )

        # Avoid recursive save via post_save signal
        type(hostel).objects.filter(pk=hostel.pk).update(
            total_rooms_count=counts['total'],
            available_rooms_count=counts['available'],
        )

        logger.info(
            f"Updated room counts for hostel {hostel.name} "
            f"(total={counts['total']}, available={counts['available']})"
        )
    except Exception as e:
        logger.error(f"Failed to update hostel room counts: {str(e)}")


# --------------------------------------------------
# Enforce single cover image per room
# --------------------------------------------------
@receiver(pre_save, sender=RoomImage)
def enforce_single_cover(sender, instance, **kwargs):
    """
    Ensures that only one image is marked as 'is_cover' for any given room.
    """
    if instance.is_cover and instance.room_id:
        # Use update() to bypass signals and prevent recursion
        RoomImage.objects.filter(
            room_id=instance.room_id,
            is_cover=True
        ).exclude(pk=instance.pk).update(is_cover=False)


# --------------------------------------------------
# Cleanup image file on delete
# --------------------------------------------------
@receiver(post_delete, sender=RoomImage)
def delete_room_image_file(sender, instance, **kwargs):
    """
    Deletes the physical image file from storage when a RoomImage record is deleted.
    """
    if instance.image:
        try:
            instance.image.delete(save=False)
            logger.info(
                f"Deleted physical image file for Room ID {instance.room_id}"
            )
        except Exception as e:
            logger.error(f"Error deleting image file: {str(e)}")
