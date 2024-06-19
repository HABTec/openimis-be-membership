import base64
from django.test import TestCase, Client
from django.contrib.auth.models import User
from graphene.test import Client as GrapheneClient
from your_app_name.schema import schema
from your_app_name.models import Insuree, Family

class GeneratePdfSlipTestCase(TestCase):
    def setUp(self):
        self.client = GrapheneClient(schema)
        self.django_client = Client()

        # Create a test user
        self.user = User.objects.create_user(username='testuser', password='testpass')
        
        # Create test data
        self.family = Family.objects.create(uuid="test-family-uuid")
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
        self.django_client.login(username='testuser', password='testpass')

        mutation = '''
        mutation {
          generate_pdf_slip(familyUuid: "test-family-uuid") {
            base64Pdf
          }
        }
        '''

        # Obtain the token for authenticated request
        response = self.client.execute(
            mutation,
            context_value={'request': self.django_client.request()}
        )
        self.assertNotIn('errors', response)
        self.assertIn('base64Pdf', response['data']['generate_pdf_slip'])
        self.assertTrue(response['data']['generate_pdf_slip']['base64Pdf'])

        # Decode the base64 PDF to ensure it's valid
        pdf_content = base64.b64decode(response['data']['generate_pdf_slip']['base64Pdf'])
        self.assertGreater(len(pdf_content), 0)

#python manage.py test your_app_name.tests.test_schema
