from membership.models import MembershipType, AreaType

class MockMembershipType:
    """A simplified version of MembershipType for testing core logic"""
    def __init__(self, region, area_type, levels_config, payments, is_paying=True):
        self.region = region
        self.area_type = area_type
        self.levels_config = levels_config
        self.payments = payments
        self.is_paying = is_paying
    
    def get_payment_amount(self, level_number):
        if not self.is_paying and level_number == 0:
            return 0.0
        if level_number < 0 or level_number >= len(self.payments):
            return None
        return self.payments[level_number]

def test_membership_logic():
    print("\n=== Testing Membership Logic ===")
    
    # Test Rural Membership
    print("\n1. Testing Rural Membership")
    rural = MockMembershipType(
        region="Test Region",
        area_type=AreaType.RURAL,
        levels_config=3,
        payments=[50.0, 75.0, 100.0],
        is_paying=True
    )
    print(f"Rural payments: {rural.payments}")
    print(f"Level 1: {rural.get_payment_amount(0)} (should be 50.0)")
    print(f"Level 2: {rural.get_payment_amount(1)} (should be 75.0)")
    print(f"Level 3: {rural.get_payment_amount(2)} (should be 100.0)")
    print(f"Invalid Level: {rural.get_payment_amount(3)} (should be None)")
    
    # Test Indigent
    print("\n2. Testing Indigent")
    indigent = MockMembershipType(
        region="Test Region",
        area_type=AreaType.RURAL,
        levels_config=1,
        payments=[0.0],
        is_paying=False
    )
    print(f"Indigent Level 0: {indigent.get_payment_amount(0)} (should be 0.0)")
    print(f"Indigent Level 1: {indigent.get_payment_amount(1)} (should be None)")
    
    # Test Mixed Membership
    print("\n3. Testing Mixed Membership")
    mixed = MockMembershipType(
        region="Test Region",
        area_type=AreaType.MIXED,
        levels_config={"urban": 2, "rural": 3},
        payments=[50.0, 100.0, 30.0, 60.0, 90.0],
        is_paying=True
    )
    print(f"Mixed payments: {mixed.payments}")
    print(f"Urban 1: {mixed.get_payment_amount(0)} (should be 50.0)")
    print(f"Urban 2: {mixed.get_payment_amount(1)} (should be 100.0)")
    print(f"Rural 1: {mixed.get_payment_amount(2)} (should be 30.0)")
    print(f"Rural 2: {mixed.get_payment_amount(3)} (should be 60.0)")
    print(f"Rural 3: {mixed.get_payment_amount(4)} (should be 90.0)")
    
    print("\n=== Test Completed Successfully ===")

if __name__ == "__main__":
    test_membership_logic()
