import base64
import json
from django.test import TestCase, Client
from graphene.test import Client as GrapheneClient
from insuree.models import Insuree, Family
from core.schema import schema  # Import the schema from your schema.py file
from .models import MembershipType, AreaType

class GeneratePdfSlipTestCase(TestCase):
    def setUp(self):
        self.client = GrapheneClient(schema)
        self.django_client = Client()

        # Create test data if not present
        if not Family.objects.filter(uuid="test-family-uuid").exists():
            self.family = Family.objects.create(uuid="test-family-uuid")
        
        if not Insuree.objects.filter(uuid="test-insuree-uuid").exists():
            self.insuree = Insuree.objects.create(
                uuid="test-insuree-uuid", 
                family=self.family, 
                chf_id="123456789", 
                head=True
            )

    def test_generate_pdf_slip_unauthenticated(self):
        mutation = '''
        mutation {
          generate_pdf_slip(familyUuid: "test-family-uuid") {
            base64Pdf
          }
        }
        '''
        response = self.client.execute(mutation)
        self.assertIn('errors', response)
        self.assertEqual(response['errors'][0]['message'], 'You do not have permission to access this resource.')

    def test_generate_pdf_slip_authenticated(self):
        # Ensure there is at least one Insuree in the database
        insuree = Insuree.objects.first()
        family_uuid = insuree.family.uuid if insuree else "test-family-uuid"

        mutation = f'''
        mutation {{
          generate_pdf_slip(familyUuid: "{family_uuid}") {{
            base64Pdf
          }}
        }}
        '''

        # Perform the GraphQL mutation
        response = self.client.execute(mutation)
        self.assertNotIn('errors', response)
        self.assertIn('base64Pdf', response['data']['generate_pdf_slip'])
        self.assertTrue(response['data']['generate_pdf_slip']['base64Pdf'])

        # Decode the base64 PDF to ensure it's valid
        pdf_content = base64.b64decode(response['data']['generate_pdf_slip']['base64Pdf'])
        self.assertGreater(len(pdf_content), 0)



class MembershipTypeTestCase(TestCase):
    def setUp(self):
        # Create test data
        self.rural_membership = MembershipType.objects.create(
            region="Test Region",
            area_type=AreaType.RURAL,
            levels_config=3,  # 3 levels for rural
            payments=[50.0, 75.0, 100.0],
            is_paying=True
        )
        
        self.urban_membership = MembershipType.objects.create(
            region="Test Region",
            area_type=AreaType.URBAN,
            levels_config=2,  # 2 levels for urban
            payments=[100.0, 150.0],
            is_paying=True
        )
        
        self.mixed_membership = MembershipType.objects.create(
            region="Test Region",
            area_type=AreaType.MIXED,
            levels_config={"urban": 2, "rural": 3},  # 2 urban + 3 rural levels
            payments=[50.0, 100.0, 30.0, 60.0, 90.0],  # First 2 are urban, last 3 are rural
            is_paying=True
        )
    
    def test_rural_membership_creation(self):
        """Test rural membership type creation and indigent auto-creation"""
        self.assertEqual(self.rural_membership.area_type, AreaType.RURAL)
        self.assertEqual(self.rural_membership.levels_config, 3)
        self.assertEqual(len(self.rural_membership.payments), 3)
        
        # Check that indigent membership was created
        indigent = MembershipType.objects.get(
            region="Test Region",
            area_type=AreaType.RURAL,
            is_paying=False
        )
        self.assertIsNotNone(indigent)
        self.assertEqual(indigent.levels_config, 1)
        self.assertEqual(indigent.payments, [0.0])
    
    def test_mixed_membership_payments(self):
        """Test payment calculation for mixed membership type"""
        # Test urban levels (1-2)
        self.assertEqual(
            MembershipType.get_membership_payment("Test Region", AreaType.MIXED, 1),
            50.0  # First urban level
        )
        self.assertEqual(
            MembershipType.get_membership_payment("Test Region", AreaType.MIXED, 2),
            100.0  # Second urban level
        )
        
        # Test rural levels (3-5)
        self.assertEqual(
            MembershipType.get_membership_payment("Test Region", AreaType.MIXED, 3),
            30.0  # First rural level
        )
        self.assertEqual(
            MembershipType.get_membership_payment("Test Region", AreaType.MIXED, 4),
            60.0  # Second rural level
        )
        self.assertEqual(
            MembershipType.get_membership_payment("Test Region", AreaType.MIXED, 5),
            90.0  # Third rural level
        )
        
        # Test indigent (level 0)
        self.assertEqual(
            MembershipType.get_membership_payment("Test Region", AreaType.MIXED, 0),
            0.0  # Indigent level
        )
        
        # Test invalid level
        self.assertIsNone(
            MembershipType.get_membership_payment("Test Region", AreaType.MIXED, 6)
        )
    
    def test_validation(self):
        """Test model validation"""
        # Test invalid levels_config for rural
        with self.assertRaises(Exception):
            MembershipType.objects.create(
                region="Invalid Region",
                area_type=AreaType.RURAL,
                levels_config="not an integer",
                payments=[10.0],
                is_paying=True
            )
        
        # Test invalid payments length
        with self.assertRaises(Exception):
            MembershipType.objects.create(
                region="Invalid Region",
                area_type=AreaType.RURAL,
                levels_config=2,
                payments=[10.0],  # Should have 2 payments
                is_paying=True
            )
        
        # Test invalid mixed levels_config
        with self.assertRaises(Exception):
            MembershipType.objects.create(
                region="Invalid Region",
                area_type=AreaType.MIXED,
                levels_config={"urban": 1},  # Missing rural
                payments=[10.0],
                is_paying=True
            )

# To run the tests, use the following command:
# python manage.py test membership.tests
