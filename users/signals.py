import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

from hostels.models import Hostel, HostelImage, HostelFacility
from rooms.models import Room, RoomImage, RoomFacility
from mess.models import Home, HomeImage, MessMenu, MealPlan, DeliveryArea, ProviderFeature

logger = logging.getLogger(__name__)

# --------------------------------------------------
# Cache keys & Configuration
# --------------------------------------------------
HOSTEL_LIST_CACHE_KEY = "hostel_list_cache"
HOSTEL_DETAIL_CACHE_PREFIX = "hostel_detail_"

MESS_LIST_CACHE_KEY = "mess_provider_list_cache"
MESS_DETAIL_CACHE_PREFIX = "mess_provider_detail_"

# --------------------------------------------------
# Cache Helper Functions (Hostels)
# --------------------------------------------------
def clear_hostel_caches(hostel_id=None):
    """
    Clears the hostel list cache and optionally a specific hostel's detail cache.
    """
    cache.delete(HOSTEL_LIST_CACHE_KEY)
    if hostel_id:
        cache.delete(f"{HOSTEL_DETAIL_CACHE_PREFIX}{hostel_id}")
    logger.debug(f"Cleared hostel caches for ID: {hostel_id}")

# --------------------------------------------------
# Cache Helper Functions (Mess)
# --------------------------------------------------
def clear_mess_caches(home_id=None):
    """
    Clears the mess provider list cache and optionally a specific provider's detail cache.
    """
    cache.delete(MESS_LIST_CACHE_KEY)
    if home_id:
        cache.delete(f"{MESS_DETAIL_CACHE_PREFIX}{home_id}")
    logger.debug(f"Cleared mess caches for ID: {home_id}")

# --------------------------------------------------
# Hostel-related Signals
# --------------------------------------------------
@receiver([post_save, post_delete], sender=Hostel)
def on_hostel_change(sender, instance, **kwargs):
    clear_hostel_caches(instance.id)

@receiver([post_save, post_delete], sender=HostelImage)
@receiver([post_save, post_delete], sender=HostelFacility)
def on_hostel_related_change(sender, instance, **kwargs):
    clear_hostel_caches(instance.hostel_id)

@receiver([post_save, post_delete], sender=Room)
def on_room_change(sender, instance, **kwargs):
    clear_hostel_caches(instance.hostel_id)

@receiver([post_save, post_delete], sender=RoomImage)
@receiver([post_save, post_delete], sender=RoomFacility)
def on_room_related_change(sender, instance, **kwargs):
    if instance.room_id:
        # Avoid direct room.hostel_id if possible to avoid extra queries, 
        # but here we need it. 
        try:
            clear_hostel_caches(instance.room.hostel_id)
        except Exception as e:
            logger.warning(f"Failed to clear hostel cache for room-related change: {e}")

# --------------------------------------------------
# Mess-related Signals
# --------------------------------------------------
@receiver([post_save, post_delete], sender=Home)
def on_home_change(sender, instance, **kwargs):
    clear_mess_caches(instance.id)

@receiver([post_save, post_delete], sender=HomeImage)
@receiver([post_save, post_delete], sender=MessMenu)
def on_home_related_change(sender, instance, **kwargs):
    if hasattr(instance, "home_id"):
        clear_mess_caches(instance.home_id)
    elif hasattr(instance, "provider") and isinstance(instance.provider, Home):
        clear_mess_caches(instance.provider.id)

# --------------------------------------------------
# Generic FK Signals (MealPlan, DeliveryArea, etc.)
# --------------------------------------------------
@receiver([post_save, post_delete], sender=MealPlan)
@receiver([post_save, post_delete], sender=DeliveryArea)
@receiver([post_save, post_delete], sender=ProviderFeature)
def on_generic_provider_change(sender, instance, **kwargs):
    """
    Handles cache clearing for objects linked via GenericForeignKey to either 
    Hostel or Home (Mess Provider).
    """
    provider = getattr(instance, "provider", None)
    if not provider:
        return

    if isinstance(provider, Hostel):
        clear_hostel_caches(provider.id)
    elif isinstance(provider, Home):
        clear_mess_caches(provider.id)
