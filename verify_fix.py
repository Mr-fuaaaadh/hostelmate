import os
import sys
import django
from django.conf import settings

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hostelmate.settings')
django.setup()

from rooms.serializers import RoomWriteSerializer
from rooms.models import Room
from django.http import QueryDict

def test_json_update_no_extras():
    print("Testing JSON update with no extra fields...")
    # Mock data
    data = {
        "room_number": "101",
        "room_type": "single",
        "capacity": 1,
        "daily_price": "500.00",
        "monthly_price": "14000.00",
        "hostel": 1
    }
    
    serializer = RoomWriteSerializer()
    try:
        internal_data = serializer.to_internal_value(data)
        print(f"Success: to_internal_value handled JSON dict. Internal data: {internal_data}")
        
        # Test if popping works (simulating update)
        d_img = internal_data.pop("deleted_images", [])
        d_fac = internal_data.pop("deleted_facilities", [])
        print(f"Success: Popped deleted fields with defaults. Images: {d_img}, Facilities: {d_fac}")
    except Exception as e:
        print(f"Error: testing JSON logic failed: {e}")
        raise e

def test_querydict_update_comma_separated():
    print("Testing QueryDict update with comma separated strings...")
    qd = QueryDict(mutable=True)
    qd.update({
        "room_number": "102",
        "facility": "1,2,3",
        "deleted_images": "4,5"
    })
    
    serializer = RoomWriteSerializer()
    # to_internal_value should convert "1,2,3" -> ["1", "2", "3"]
    internal_data = serializer.to_internal_value(qd)
    
    if isinstance(internal_data.get('facility'), list) and internal_data.get('facility') == ['1', '2', '3']:
        print("Success: Facility string converted to list in QueryDict.")
    else:
        print(f"Error: Internal data conversion failed: {internal_data}")
        raise ValueError("Conversion failed")

if __name__ == "__main__":
    try:
        # We don't actually need to run it against the real DB to test the serializer logic
        test_json_update_no_extras()
        test_querydict_update_comma_separated()
        print("\nAll verification tests passed!")
    except Exception as e:
        print(f"\nVerification failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
