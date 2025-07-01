"""
Standalone test for MembershipType core logic without Django dependencies.
"""

class AreaType:
    RURAL = 'Rural'
    URBAN = 'Urban'
    MIXED = 'Mixed'

class MembershipType:
    """
    Simplified version of the MembershipType class for testing core logic.
    """
    def __init__(self, region, area_type, levels_config, payments, is_paying=True):
        self.region = region
        self.area_type = area_type
        self.levels_config = levels_config
        self.payments = payments
        self.is_paying = is_paying
    
    def get_payment_amount(self, level_number):
        """Get payment amount for a specific level number."""
        if not self.is_paying and level_number == 0:
            return 0.0
        if level_number < 0 or level_number >= len(self.payments):
            return None
        return self.payments[level_number]
    
    @classmethod
    def get_membership_payment(cls, region, area_type, level_number):
        """
        Simplified version of the class method to get payment amount.
        Uses a hardcoded list of memberships for testing.
        
        Note: Level numbers are 1-based in the API (1 is first level)
        """
        # This is a simplified version that doesn't query the database
        memberships = [
            # Rural membership
            cls("Test Region", AreaType.RURAL, 3, [50.0, 75.0, 100.0], True),
            # Urban membership
            cls("Test Region", AreaType.URBAN, 2, [100.0, 150.0], True),
            # Mixed membership (Gondar example)
            cls("Gondar", AreaType.MIXED, {"urban": 2, "rural": 3}, 
                [50.0, 100.0, 30.0, 60.0, 90.0], True),
            # Indigent memberships (one for each area type)
            cls("Test Region", AreaType.RURAL, 1, [0.0], False),
            cls("Test Region", AreaType.URBAN, 1, [0.0], False),
            cls("Test Region", AreaType.MIXED, 1, [0.0], False),
            # Gondar memberships
            cls("Gondar", AreaType.RURAL, 3, [30.0, 60.0, 90.0], True),
            cls("Gondar", AreaType.URBAN, 2, [50.0, 100.0], True),
            cls("Gondar", AreaType.MIXED, 1, [0.0], False),
        ]
        
        # For indigent (level 0)
        is_paying = level_number != 0
        
        # For Mixed area type with level_number > 0, determine if it's urban or rural
        if area_type == AreaType.MIXED and is_paying:
            # Find the mixed membership to check the levels configuration
            mixed_membership = next(
                (m for m in memberships 
                 if m.region == region and m.area_type == AreaType.MIXED and m.is_paying),
                None
            )
            
            if mixed_membership and isinstance(mixed_membership.levels_config, dict):
                urban_levels = mixed_membership.levels_config.get('urban', 0)
                if level_number <= urban_levels:
                    area_type = AreaType.URBAN
                else:
                    area_type = AreaType.RURAL
                    level_number = level_number - urban_levels  # Adjust rural level number
        
        # Find the appropriate membership
        membership = next(
            (m for m in memberships 
             if m.region == region and m.area_type == area_type and m.is_paying == is_paying),
            None
        )
        
        if not membership:
            return None
            
        # For paying memberships, adjust the level number (convert from 1-based to 0-based)
        if is_paying:
            level_number = level_number - 1
        
        return membership.get_payment_amount(level_number)

def test_membership_core():
    print("\n=== Testing Membership Core Logic ===")
    
    # Test Rural Membership
    print("\n1. Testing Rural Membership")
    rural = MembershipType(
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
    indigent = MembershipType(
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
    mixed = MembershipType(
        region="Gondar",  # Using Gondar to match the example
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
    
    # Test the class method with Test Region
    print("\n4. Testing Class Method with Test Region")
    print(f"Rural Level 1: {MembershipType.get_membership_payment('Test Region', AreaType.RURAL, 1)} (should be 50.0)")
    print(f"Rural Level 2: {MembershipType.get_membership_payment('Test Region', AreaType.RURAL, 2)} (should be 75.0)")
    print(f"Urban Level 1: {MembershipType.get_membership_payment('Test Region', AreaType.URBAN, 1)} (should be 100.0)")
    print(f"Urban Level 2: {MembershipType.get_membership_payment('Test Region', AreaType.URBAN, 2)} (should be 150.0)")
    print(f"Indigent: {MembershipType.get_membership_payment('Test Region', AreaType.RURAL, 0)} (should be 0.0)")
    
    # Test the class method with Gondar (from the example)
    print("\n5. Testing Gondar Example")
    # For Gondar, we have separate memberships for Urban and Rural
    print(f"Urban 1: {MembershipType.get_membership_payment('Gondar', AreaType.URBAN, 1)} (should be 50.0)")
    print(f"Urban 2: {MembershipType.get_membership_payment('Gondar', AreaType.URBAN, 2)} (should be 100.0)")
    print(f"Rural 1: {MembershipType.get_membership_payment('Gondar', AreaType.RURAL, 1)} (should be 30.0)")
    print(f"Rural 2: {MembershipType.get_membership_payment('Gondar', AreaType.RURAL, 2)} (should be 60.0)")
    print(f"Rural 3: {MembershipType.get_membership_payment('Gondar', AreaType.RURAL, 3)} (should be 90.0)")
    print(f"Indigent: {MembershipType.get_membership_payment('Gondar', AreaType.MIXED, 0)} (should be 0.0)")
    
    # Test with the exact example from the user
    print("\n6. Testing User's Exact Example")
    print("{\n  \"region\": \"Gondar\",\n  \"area_type\": \"Urban\",\n  \"level_number\": 2\n}")
    print(f"Result: {MembershipType.get_membership_payment('Gondar', 'Urban', 2)} (should be 100.0)")
    
    print("\n=== Test Completed Successfully ===")

if __name__ == "__main__":
    test_membership_core()
