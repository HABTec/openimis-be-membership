import base64
from django.test import TestCase, Client
from graphene.test import Client as GrapheneClient
from insuree.models import Insuree, Family
from core.schema import schema  # Import the schema from your schema.py file

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

# To run the tests, use the following command:
# python manage.py test your_app_name.tests.tests
