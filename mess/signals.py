from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Home, HomeImage, MessMenu, DeliveryArea, MealPlan, ProviderFeature
import logging

logger = logging.getLogger(__name__)


# -----------------------------
# Log Home creation / update
# -----------------------------
@receiver(post_save, sender=Home)
def log_home_saved(sender, instance, created, **kwargs):
    if created:
        logger.info(f"Home created: {instance.name} by {instance.owner.email}")
    else:
        logger.info(f"Home updated: {instance.name}")


# -----------------------------
# Cleanup HomeImage on delete
# -----------------------------
@receiver(post_delete, sender=HomeImage)
def delete_home_image_file(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)
        logger.info(f"Deleted HomeImage {instance.id} for {instance.home.name}")


# -----------------------------
# Optional: mess menus / delivery areas / meal plans / features logging
# -----------------------------
@receiver(post_save, sender=MessMenu)
def log_mess_menu(sender, instance, created, **kwargs):
    logger.info(f"MessMenu {'created' if created else 'updated'} for {instance.provider}")


@receiver(post_delete, sender=MessMenu)
def delete_mess_menu(sender, instance, **kwargs):
    logger.info(f"MessMenu deleted for {instance.provider}")
