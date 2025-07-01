import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

# Mock the necessary Django imports
import django
django.conf.settings.configure(
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    },
    INSTALLED_APPS=[
        'django.contrib.contenttypes',
        'django.contrib.auth',
        'membership',
    ],
    DEFAULT_AUTO_FIELD='django.db.models.BigAutoField',
)

django.setup()

# Now we can import our model
from membership.models import MembershipType, AreaType

def test_membership_type():
    print("\n=== Testing MembershipType Model ===")
    
    # Test Rural Membership
    print("\n1. Testing Rural Membership")
    rural = MembershipType(
        region="Test Region",
        area_type=AreaType.RURAL,
        levels_config=3,
        payments=[50.0, 75.0, 100.0],
        is_paying=True
    )
    rural.save()
    print(f"Created Rural Membership: {rural}")
    
    # Test Urban Membership
    print("\n2. Testing Urban Membership")
    urban = MembershipType(
        region="Test Region",
        area_type=AreaType.URBAN,
        levels_config=2,
        payments=[100.0, 150.0],
        is_paying=True
    )
    urban.save()
    print(f"Created Urban Membership: {urban}")
    
    # Test Mixed Membership
    print("\n3. Testing Mixed Membership")
    mixed = MembershipType(
        region="Test Region",
        area_type=AreaType.MIXED,
        levels_config={"urban": 2, "rural": 3},
        payments=[50.0, 100.0, 30.0, 60.0, 90.0],
        is_paying=True
    )
    mixed.save()
    print(f"Created Mixed Membership: {mixed}")
    
    # Test payment calculation
    print("\n4. Testing Payment Calculation")
    print(f"Rural Level 1: {MembershipType.get_membership_payment('Test Region', AreaType.RURAL, 1)}")
    print(f"Urban Level 2: {MembershipType.get_membership_payment('Test Region', AreaType.URBAN, 2)}")
    print(f"Mixed Urban 1: {MembershipType.get_membership_payment('Test Region', AreaType.MIXED, 1)}")
    print(f"Mixed Rural 1: {MembershipType.get_membership_payment('Test Region', AreaType.MIXED, 3)}")
    print(f"Indigent: {MembershipType.get_membership_payment('Test Region', AreaType.RURAL, 0)}")
    
    # Test getting payment for non-existent region
    print(f"\n5. Testing non-existent region: {MembershipType.get_membership_payment('Non-Existent', AreaType.RURAL, 1)}")
    
    print("\n=== Test Completed Successfully ===")

if __name__ == "__main__":
    test_membership_type()
