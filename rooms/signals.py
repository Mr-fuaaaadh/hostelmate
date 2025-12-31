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
    if not instance.hostel_id:
        return

    hostel = instance.hostel

    total_rooms = hostel.rooms.count()
    available_rooms = hostel.rooms.filter(is_available=True).count()

    # Avoid recursive save
    type(hostel).objects.filter(pk=hostel.pk).update(
        total_rooms_count=total_rooms,
        available_rooms_count=available_rooms,
    )

    logger.info(
        f"Updated room counts for hostel {hostel.name} "
        f"(total={total_rooms}, available={available_rooms})"
    )


# --------------------------------------------------
# Enforce single cover image per room
# --------------------------------------------------
@receiver(pre_save, sender=RoomImage)
def enforce_single_cover(sender, instance, **kwargs):
    if instance.is_cover and instance.room_id:
        RoomImage.objects.filter(
            room_id=instance.room_id,
            is_cover=True
        ).exclude(pk=instance.pk).update(is_cover=False)


# --------------------------------------------------
# Cleanup image file on delete
# --------------------------------------------------
@receiver(post_delete, sender=RoomImage)
def delete_room_image_file(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)

    if instance.room_id:
        logger.info(
            f"Deleted image for room {instance.room.room_number} "
            f"in hostel {instance.room.hostel.name}"
        )
