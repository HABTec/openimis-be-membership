import os
import django
import sys

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openimis.settings')
django.setup()

from membership.models import MembershipType, AreaType

def test_membership_creation():
    print("\n=== Testing Membership Type Creation ===")
    
    # Test Rural Membership
    rural = MembershipType.objects.create(
        region="Test Region",
        area_type=AreaType.RURAL,
        levels_config=3,
        payments=[50.0, 75.0, 100.0],
        is_paying=True
    )
    print(f"Created Rural Membership: {rural}")
    
    # Test Urban Membership
    urban = MembershipType.objects.create(
        region="Test Region",
        area_type=AreaType.URBAN,
        levels_config=2,
        payments=[100.0, 150.0],
        is_paying=True
    )
    print(f"Created Urban Membership: {urban}")
    
    # Test Mixed Membership
    mixed = MembershipType.objects.create(
        region="Test Region",
        area_type=AreaType.MIXED,
        levels_config={"urban": 2, "rural": 3},
        payments=[50.0, 100.0, 30.0, 60.0, 90.0],
        is_paying=True
    )
    print(f"Created Mixed Membership: {mixed}")
    
    # Test payment calculation
    print("\n=== Testing Payment Calculation ===")
    print(f"Rural Level 1: {MembershipType.get_membership_payment('Test Region', AreaType.RURAL, 1)}")
    print(f"Urban Level 2: {MembershipType.get_membership_payment('Test Region', AreaType.URBAN, 2)}")
    print(f"Mixed Urban 1: {MembershipType.get_membership_payment('Test Region', AreaType.MIXED, 1)}")
    print(f"Mixed Rural 1: {MembershipType.get_membership_payment('Test Region', AreaType.MIXED, 3)}")
    print(f"Indigent: {MembershipType.get_membership_payment('Test Region', AreaType.RURAL, 0)}")
    
    # Clean up
    MembershipType.objects.all().delete()
    print("\nTest data cleaned up")

if __name__ == "__main__":
    test_membership_creation()
