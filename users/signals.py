from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

from hostels.models import Hostel, HostelImage, HostelFacility
from rooms.models import Room, RoomImage, RoomFacility
from mess.models import MealPlan, DeliveryArea

# --------------------------------------------------
# Cache keys
# --------------------------------------------------
HOSTEL_LIST_CACHE_KEY = "hostel_list_cache"
HOSTEL_DETAIL_CACHE_PREFIX = "hostel_detail_"

# --------------------------------------------------
# Helper functions
# --------------------------------------------------
def clear_hostel_list_cache():
    cache.delete(HOSTEL_LIST_CACHE_KEY)

def clear_hostel_detail_cache(hostel_id):
    if hostel_id:
        cache.delete(f"{HOSTEL_DETAIL_CACHE_PREFIX}{hostel_id}")

def clear_all(hostel_id):
    clear_hostel_list_cache()
    clear_hostel_detail_cache(hostel_id)

# --------------------------------------------------
# Hostel
# --------------------------------------------------
@receiver([post_save, post_delete], sender=Hostel)
def hostel_cache_clear(sender, instance, **kwargs):
    clear_all(instance.id)

# --------------------------------------------------
# Hostel Images & Facilities
# --------------------------------------------------
@receiver([post_save, post_delete], sender=HostelImage)
@receiver([post_save, post_delete], sender=HostelFacility)
def hostel_related_cache_clear(sender, instance, **kwargs):
    clear_all(instance.hostel_id)

# --------------------------------------------------
# Rooms
# --------------------------------------------------
@receiver([post_save, post_delete], sender=Room)
def room_cache_clear(sender, instance, **kwargs):
    clear_all(instance.hostel_id)

# --------------------------------------------------
# Room Images & Facilities
# --------------------------------------------------
@receiver([post_save, post_delete], sender=RoomImage)
@receiver([post_save, post_delete], sender=RoomFacility)
def room_related_cache_clear(sender, instance, **kwargs):
    if instance.room_id:
        clear_all(instance.room.hostel_id)

# --------------------------------------------------
# Meal Plans & Delivery Areas (Generic FK)
# --------------------------------------------------
@receiver([post_save, post_delete], sender=MealPlan)
@receiver([post_save, post_delete], sender=DeliveryArea)
def meal_delivery_cache_clear(sender, instance, **kwargs):
    """
    provider is Hostel or Home (GenericForeignKey)
    Only clear if provider is Hostel
    """
    provider = getattr(instance, "provider", None)

    if provider and isinstance(provider, Hostel):
        clear_all(provider.id)
