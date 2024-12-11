# 1. Standard Library Imports
import random
import time
import hashlib
from datetime import datetime, timedelta

# 2. Third-Party Imports
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework_simplejwt.authentication import JWTAuthentication as SimpleJWTAuthentication

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import generics

from wkhtmltopdf.views import PDFTemplateView

# 3. Django Imports
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import (
    check_password, is_password_usable, make_password
)
from django.core.cache import cache
from django.db import transaction
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render
from django.utils.crypto import get_random_string
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

# 4. Local App Imports
from core.models import User, Role, UserRole, InteractiveUser, Language, Officer
from core.schema import update_or_create_user
from core.services.userServices import set_user_password
from insuree.models import (
    Family, Insuree, InsureePhoto, InsureePolicy, Gender, Relation
)
from location import models as location_models
from membership.apps import MembershipCardConfig
from membership.utils.db_helper import SQLiteHelper  # Specific class import to be clear
from membership.utils.generic_response_utils import error_response, success_response
from .permission import IsInsuree 
from django.core.exceptions import ObjectDoesNotExist
from claim.models import Claim, ClaimItem, ClaimService

from .services import (
    PDFGenerationService,
    create_insuree_and_family,
    create_insuree_policy,
    create_contribution
)



from .serializers import (
    SignInSerializer,
    # PolicySerializer,
    InsureeSerializer,
    FamilySerializer,
    LocationSerializer,
    HospitalSerializer,
    InsureePolicySerializer,
    UserRegistrationSerializer,
    ClaimSerializer

)


class UserSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=15)

    def create(self, validated_data):
        # Extract username and email from input data
        username = validated_data['username']
        email = validated_data.get('email', 'kadl.invoker@hotmail.com')
        # import pdb;pdb.set_trace()
        # import pdb; pdb.set_trace()
        # Generate a password and salt for InteractiveUser
        raw_password =validated_data.get('password')
        salt = get_random_string(16)
        # Create the InteractiveUser instance
        interactive_user = InteractiveUser.objects.create(
            login_name=username,
            email=email,
            private_key=salt,
            # password=hashed_password,
            last_name="abcd-testa",  # Adjust based on your requirements
            other_names="abcd-testa",
            audit_user_id = -1,
            role_id=1,
            language=Language.objects.first(),  # Set the appropriate LanguageID
        )

        interactive_user.set_password(raw_password)
        user = User.objects.create(
            username=username,
            i_user=interactive_user
        )
        return interactive_user, user



class UsernameExistsView(APIView):
    def post(self, request):
        # Get the 'username' from the request data
        username = request.data.get('username')

        if not username:
            return Response(
                {'error': 'Username is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if the username already exists
        if User.objects.filter(username=username).exists():
            return Response(
                {'message': 'Username is already taken'},
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            return Response(
                {'message': 'Username is available'},
                status=status.HTTP_200_OK
            )

def create_insuree_user(data):
    """Helper function to create an 'insuree' user."""
    insuree_role, _ = Role.objects.get_or_create(name="insuree", is_system=True, is_blocked=False)
    password = data.get('password')

    if not password:
        return {"error": "Password is required"}, status.HTTP_400_BAD_REQUEST

    # hashed_password = make_password(password)
    user_data = {
        "username": data.get("username"),
        "password": data.get("password"),
        "phone": data.get("phone"),
        "email": data.get("email"),
    }

    serializer = UserSerializer(data=user_data)
    # import pdb;pdb.set_trace()
    if serializer.is_valid():
        interactive_user, user = serializer.save()
        UserRole.objects.create(user=interactive_user, role=insuree_role)
        phone = data.get('phone')
        db_helper = SQLiteHelper()
        #print("user", user.__dict__, "i_user", interactive_user.__dict__)
        db_helper.update_user_id_by_phone(phone, user.i_user_id)  # Update the user_id in SQLite
        db_helper.close()
        return {"message": "User with 'insuree' role created successfully."}, status.HTTP_201_CREATED
    return serializer.errors, status.HTTP_400_BAD_REQUEST



def send_otp(otp, phone=None, email=None):
    import requests
    # Looking to send emails in production? Check out our Email API/SMTP product!
    url = "https://sandbox.api.mailtrap.io/api/send/3221599"
    
    payload = {
        "from": {"email": "hello@openimis.org", "name": "openIMIS"},
        "to": [{"email": "sunilparajuli2002@gmail.com"}],
        "subject": f"Dear {phone if phone else email},  Your OTP code is!",
        "text": f"Your OTP code is: {otp}!, Do not share it with anyone",
        "category": "Integration Test"
    }
    
    headers = {
        "Authorization": "Bearer d17417198e534b959b00c39229682340",
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json=payload)

    print(response.status_code, response.text)


class RegisterAPIView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            chfid = data['chfid']
            head_chfid = data['head_chfid']
            dob = data['dob']
            phone = data['phone']
            email = data['email']

            # Check if the Insuree exists
            try:
                head_insuree = Insuree.objects.get(chf_id=head_chfid, head=True)
                insuree = Insuree.objects.get(
                    chf_id=chfid, family=head_insuree.family, dob=dob
                )
            except Insuree.DoesNotExist:
                return Response(
                    {"error": "Insuree with the provided details does not exist."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Update phone and email if provided
            if phone:
                insuree.phone = phone
            if email:
                insuree.email = email
            insuree.save()

            # Generate OTP and store it in SQLite
            otp_code = str(random.randint(100000, 999999))  # 6-digit OTP
            db = SQLiteHelper()
            db.insert_user(insuree.id, phone, otp_code)
            db.close()

            # Simulate sending OTP (for now, just print it)
            print(f"OTP for {phone}: {otp_code}")
            try:
                pass
                #send_otp(otp_code, phone, email)
            except:
                pass # do nothing
            return Response(
                {"message": "OTP sent successfully."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendOTPAPIView(APIView):
    def post(self, request):
        phone = request.data.get("phone")  # Get phone number from request

        if not phone:
            return Response(
                {"error": "Phone number is required to resend OTP."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch user by phone from SQLite
        db = SQLiteHelper()
        user_data = db.get_user_by_phone(phone)  # Retrieve user data from SQLite

        if not user_data:
            db.close()
            return Response(
                {"error": "No user found with the provided phone number."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Generate a new OTP
        otp_code = str(random.randint(100000, 999999))  # 6-digit OTP

        # Update OTP in SQLite database
        print("otp_code", otp_code, "user_data", user_data)
        print(user_data[0])

        db.update_otp(user_data[0], otp_code)
        db.close()

        # Simulate sending OTP (for now, just print it)
        print(f"New OTP for {phone}: {otp_code}")
        try:
            pass
            # Uncomment and implement the send_otp function to send OTP
            # send_otp(otp_code, phone, user_data.get('email'))
        except Exception as e:
            print(f"Failed to send OTP: {e}")
            return Response(
                {"error": "Failed to send OTP. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {"message": "OTP resent successfully."},
            status=status.HTTP_200_OK
        )

class ValidateOTPAPIView(APIView):
    def post(self, request):
        phone = request.data.get('phone')
        otp_code = request.data.get('otp')
        username = request.data.get('username')
        password = request.data.get('password')
        resend = request.data.get('resend')
        # Retrieve user data from SQLite
        db = SQLiteHelper()
        user_data = db.get_user_by_phone(phone)
        db.close()

        if not user_data:
            return Response({"error": "User not found."}, status=status.HTTP_400_BAD_REQUEST)

        _, insuree_id, _, saved_otp, user_id, otp_expiry, otp_validated = user_data

        # Check OTP and expiry time
        if saved_otp != otp_code:
            return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

        if int(time.time()) > otp_expiry:
            return Response({"error": "OTP expired."}, status=status.HTTP_400_BAD_REQUEST)
        _data = request.data.copy()
        _data.update({
            "insuree_id": insuree_id,   # Add insuree ID
            "username": username,
            "password": password
        })    
        create_user_response, status_code = create_insuree_user(_data)
        # OTP is valid, proceed with registration (in your main DB)
        #return Response({"message": "OTP validated, registration complete!"}, status=status.HTTP_200_OK)
        return Response(create_user_response, status_code)
    

class PrintPdfSlipView(APIView, PDFTemplateView):
    filename = MembershipCardConfig.membership_slip_name
    template_name = MembershipCardConfig.get_template_by_os()
    cmd_options = MembershipCardConfig.wkhtml_cmd_options_for_printing
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        if not request.user:
            return HttpResponseForbidden(
                "You do not have permission to access this resource."
            )
        return super(PrintPdfSlipView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        insuree_uuid = kwargs.get("insuree_uuid")
        print("kwargs", kwargs)
        slip_type = request.GET.get("type")
        if not insuree_uuid:
            raise ValidationError("Missing 'insuree_uuid' parameter.")
        try:
            pdf_base64 = PDFGenerationService.generate_pdf(
                request.user, insuree_uuid, slip_type
            )
            response = Response(
                {
                    "pdf_base64": pdf_base64,
                    "filename": self.filename,
                    "content_type": "application/pdf",
                }
            )
            return response
        except Exception as e:
            return Response({"error": str(e)}, status=400)


def index(request):
    return render(request, "test-card.html")


class Config(APIView):
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        import os,json
        # Load configuration from mobile_config.json
        config_path = os.path.join(os.path.dirname(__file__), '..', 'mobile_config.json')

        with open(config_path, 'r', encoding='utf-8') as json_file:
            CONFIG = json.load(json_file)

        return Response(CONFIG, status=200)

class Signin(APIView):
    permission_classes = ()
    authentication_classes = ()

    def post(self, request):
        from membership.utils.auth_helper import authenticate_and_get_token
        received_json_data = request.data
        serializer = SignInSerializer(data=received_json_data)
        db_helper = SQLiteHelper()  # Assuming this is your custom DB helper class

        if not serializer.is_valid():
            return JsonResponse({"message": serializer.errors}, status=400)

        # Validate username and password
        username = received_json_data.get("username")
        password = received_json_data.get("password")
        is_officer = username.lower() == "admin"
        if not username or not password:
            return JsonResponse({"message": "Missing username or password"}, status=400)

        # Reuse the `authenticate_and_get_token` function for authentication
        try:
            user = User.objects.filter(username=username).first()
            is_insuree = db_helper.is_insuree(user.i_user_id) if user else False
            print("is_insuree", is_insuree, "user", user.i_user_id, "user_dict", user.__dict__)
            token_data = authenticate_and_get_token(username, password, request)
            insuree_info = {}
            if is_insuree:
                insuree = Insuree.objects.filter(id=user.i_user_id).first()  # Adjust field name as needed
                if insuree:
                    insuree_info = {
                        "first_name": insuree.other_names,
                        "last_name": insuree.last_name,
                        "chfid": insuree.chf_id,
                        "uuid": insuree.uuid,
                        "family": insuree.family.pk if insuree.family else None,  # Assuming family has a `name` field
                    }                
            if token_data:
                return JsonResponse(
                    {
                        "refresh": token_data["token"],  # Assuming it's a refresh token
                        "access": token_data["token"],  # Assuming the same for access
                        "username": username,
                        "exp": token_data["exp"],
                        "first_name": user._u.other_names if user and user._u else "",
                        "last_name": user._u.last_name if user and user._u else "",
                        "email": user._u.email if user and user._u and user._u.email else "",
                        "is_officer":  is_officer,#bool(user.officer_id) if user else False,
                        "is_insuree": is_insuree,
                        "insuree_info": insuree_info,
                    },
                    status=200,
                )
            else:
                return JsonResponse(
                    {"message": "Invalid username or password"}, status=403
                )
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=400)



class EnrollmentView(APIView):
    #authentication_classes = [SimpleJWTAuthentication]
    #permission_classes = [IsAuthenticated]
    @transaction.atomic
    def post(self, request):
        print("request", request.data)
        insuree = create_insuree_and_family(request) #head_insuree
        insuree_policy = create_insuree_policy(insuree)
        import pdb;pdb.set_trace()
        print("insuree", insuree)
        create_contribution(insuree_policy)
        return Response({"Success": True}, status=status.HTTP_201_CREATED)


class PolicyCreateAndUpdateAPIView(APIView):
    authentication_classes = [SimpleJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        head_chfid = request.data.get("headChfid", None)
        chfid = request.data.get("chfid", None)
        if not (head_chfid or chfid):
            return error_response(message=f"missing chfid or head chfid")
        insuree = Insuree.objects.filter(chf_id=chfid, validity_to=None).first()
        insuree_policy = InsureePolicy.objects.filter(
            insuree__chfid=request.data.get("chfid"), validity_to=None
        )
        if insuree_policy.exists():
            if insuree_policy.expiry_date >= datetime.now():
                return error_response(message="Policy already exists, and expired yet")
        else:
            insuree_policy = InsureePolicy.objects.create(
                insuree=insuree,
                Policy=insuree.family.policy,
                enrolled_date=datetime.now(),
                expiry_date=datetime.now() + timedelta(days=365),
                audit_user_id=-1,
                offline=False,
                effective_date=datetime.now(),
            )
        return success_response(message="Policy Enrolled successfully")


class InsureeInformation(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        chfid = request.GET.get("insuree", None)
        if not chfid:
            return Response(
                {"success": False, "message": "chfid is required"}, status=400
            )

        insuree = Insuree.objects.filter(chf_id=chfid, validity_to=None).first()
        if not insuree:
            return Response(
                {"success": False, "message": "insuree not found"}, status=400
            )

        data = {}
        insuree_serializer = InsureeSerializer(insuree).data
        data["insuree"] = insuree_serializer

        serialize_family = FamilySerializer(
            Family.objects.filter(id=insuree.family.id), many=True
        ).data
        data["families"] = serialize_family

        serialize_policy = InsureePolicySerializer(
            InsureePolicy.objects.filter(insuree=insuree, validity_to=None), many=True
        ).data
        data["policy"] = serialize_policy

        return Response({"success": True, "data": data}, status=200)


def build_location_tree(location):
    """
    Recursive function to build a nested location structure.
    """
    # Fetch the children of the current location
    children = location_models.Location.objects.filter(parent=location)

    # Base structure of the current location
    location_data = {
        "id": location.id,
        "uuid": location.uuid,
        "code": location.code,
        "name": location.name,
        "type": location.type,
        "male_population": location.male_population,
        "female_population": location.female_population,
        "other_population": location.other_population,
        "families": location.families,
        "district": {},
        "Municipality": {},
        "Village": {},
    }

    # Recursively build nested structure
    for child in children:
        if child.type == "D":
            location_data["district"] = build_location_tree(child)
        elif child.type == "W":
            location_data["Municipality"] = build_location_tree(child)
        elif child.type == "V":
            location_data["Village"] = build_location_tree(child)

    return location_data


class LocationAPIView(APIView):
    #permission_classes = [IsAuthenticated]
    permission_classes = []
    authentication_classes = []
    serializer_class = LocationSerializer

    def get(self, request):
        try:
            # Fetch top-level locations (with parent = null)
            top_level_locations = location_models.Location.objects.filter(
                parent__isnull=True, validity_to=None
            )

            # Build the nested structure
            location_tree = [
                build_location_tree(location) for location in top_level_locations
            ]

            # Structure the final response
            response_data = {"success": True, "data": location_tree}

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class HospitalAPIView(APIView):
    serializer_class = HospitalSerializer
    permission_classes = []#[IsAuthenticated]
    authentication_classes = []

    def get(self, request):
        # import pdb;pdb.set_trace()
        try:
            # Fetch top-level locations (with parent = null)
            hospitals = HospitalSerializer(
                location_models.HealthFacility.objects.filter(validity_to=None),
                many=True,
            )

            # Structure the final response
            response_data = {"success": True, "data": hospitals.data}

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )



class InsureeClaimsApi(generics.ListAPIView):
    # permission_classes = [IsAuthenticated, IsInsuree]
    permission_classes = [IsAuthenticated]
    serializer_class = ClaimSerializer

    def get_queryset(self):
        # Step 1: Get the current user's i_user_id
        user_id = self.request.user.i_user_id
        
        # Step 2: Use SQLiteHelper to get the insuree_id from the SQLite DB
        db_helper = SQLiteHelper()
        insuree_id = db_helper.get_insuree_id_by_user_id(user_id)
        db_helper.close()  # Close the connection to the SQLite DB
        
        # Step 3: Check if insuree_id was found
        if insuree_id:
            try:
                # Step 4: Fetch the Insuree object using insuree_id
                insuree = Insuree.objects.get(pk=insuree_id)
                
                # Step 5: Filter and return the claims for the Insuree
                return Claim.objects.filter(insuree=insuree).prefetch_related('items')
            except ObjectDoesNotExist:
                # Return an empty queryset if the Insuree is not found
                return Claim.objects.none()
        
        # Return an empty queryset if no insuree_id is found
        return Claim.objects.none()



class InsureeClaimServiceItems(APIView):
    #permission_classes = [IsAuthenticated, IsInsuree]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        claim_id = request.GET.get('claim_id')
        #claim_id=2
        user_id = self.request.user.i_user_id
        db_helper = SQLiteHelper()
        insuree_id = db_helper.get_insuree_id_by_user_id(user_id)
        db_helper.close()  
        data = {
            "claimed_items": [],
            "claimed_services": []
        }
        
        if insuree_id:
            try:
                # Fetch the Insuree object using insuree_id
                insuree = Insuree.objects.get(pk=insuree_id)
                
                # Fetch ClaimItems
                claimed_items = ClaimItem.objects.filter(claim_id=claim_id, validity_to=None)
                for ci in claimed_items:
                    data['claimed_items'].append({
                        "item_name": ci.item.name,  # Assuming `item` has a `name` field
                        "qty_provided": ci.qty_provided,
                        "price_asked": ci.price_asked,
                        "price_approved": ci.price_approved,
                        "status": ci.status
                    })
                
                # Fetch ClaimServices
                claimed_services = ClaimService.objects.filter(claim_id=claim_id, validity_to=None)
                for cs in claimed_services:
                    data['claimed_services'].append({
                        "service_name": cs.service.name,  # Assuming `service` has a `name` field
                        "qty_provided": cs.qty_provided,
                        "price_asked": cs.price_asked,
                        "price_approved": cs.price_approved,
                        "status": cs.status
                    })
                
                return Response(data)
            
            except ObjectDoesNotExist:
                # If the Insuree is not found, return an empty response
                return Response(data)
        
        # If no insuree_id is found, return an empty response
        return Response(data)


from rest_framework.test import APIRequestFactory
from api_fhir_r4.views.fhir.insuree import InsureeViewSet  # Import your InsureeViewSet
from rest_framework.test import force_authenticate


class PatientIdentifierAPIView(APIView):
    def get(self, request, *args, **kwargs):
        # Get the identifier from the query parameters
        identifier = request.GET.get("identifier")
        if not identifier:
            return Response({"error": "Identifier is required"}, status=400)

        # Find or create an admin user (ensure admin user exists)
        admin_user = authenticate(username="Admin", password="admin123")
        if not admin_user:
            return Response({"error": "Admin user not found"}, status=500)

        # Create a simulated request
        factory = APIRequestFactory()
        simulated_request = factory.get(f"/api/insuree/?identifier={identifier}")

        # Authenticate the simulated request as the admin user
        force_authenticate(simulated_request, user=admin_user)

        # Instantiate the InsureeViewSet
        viewset = InsureeViewSet.as_view({"get": "list"})  # Change to "retrieve" if you need single retrieval

        # Call the InsureeViewSet
        response = viewset(simulated_request)

        # Return the response as-is to the API client
        return response


class NationalIDView(APIView):
    authentication_classes = ()
    permission_classes = ()
    def get(self, request):
        MEMBERS = [
        {
            "national_id": "9849298499",
            "name": "Darshan Doraju",
            "firstname": "Darshan",
            "lastname": "Doraju",
            "age": 30,
            "address": "123 Main St, Springfield",
            "gender": "Male",
            "birthdate": "1993-04-15",
            "is_head": True,
            "phone": "+1234567890",
            "email": "darshan.doraju@example.com"
        },
        {
            "national_id": "9849298491",
            "name": "Jane Smith",
            "firstname": "Jane",
            "lastname": "Smith",
            "age": 25,
            "address": "456 Elm St, Metropolis",
            "gender": "Female",
            "birthdate": "1998-07-22",
            "is_head": True,
            "phone": "+1234567891",
            "email": "jane.smith@example.com"
        },
        {
            "national_id": "9849298492",
            "name": "Alice Johnson",
            "firstname": "Alice",
            "lastname": "Johnson",
            "age": 28,
            "address": "789 Oak St, Gotham",
            "gender": "Female",
            "birthdate": "1995-09-10",
            "is_head": True,
            "phone": "+1234567892",
            "email": "alice.johnson@example.com"
        },
        {
            "national_id": "9849298493",
            "name": "Bob Brown",
            "firstname": "Bob",
            "lastname": "Brown",
            "age": 35,
            "address": "321 Pine St, Star City",
            "gender": "Male",
            "birthdate": "1988-02-19",
            "is_head": True,
            "phone": "+1234567893",
            "email": "bob.brown@example.com"
        },
                {
            "national_id": "9849298494",
            "name": "Bob Brown",
            "firstname": "Bob",
            "lastname": "Brown",
            "age": 35,
            "address": "321 Pine St, Star City",
            "gender": "Male",
            "birthdate": "1988-02-19",
            "is_head": True,
            "phone": "+1234567893",
            "email": "bob.brown@example.com"
        },
        {
            "national_id": "9849298495",
            "name": "Bob Brown",
            "firstname": "Bob",
            "lastname": "Brown",
            "age": 35,
            "address": "321 Pine St, Star City",
            "gender": "Male",
            "birthdate": "1988-02-19",
            "is_head": True,
            "phone": "+1234567893",
            "email": "bob.brown@example.com"
        } ,
                {
            "national_id": "9849298496",
            "name": "asd",
            "firstname": "Bsdsdb",
            "lastname": "Brasdasdown",
            "age": 35,
            "address": "321 Pine St, Star City",
            "gender": "Male",
            "birthdate": "1988-02-19",
            "is_head": True,
            "phone": "+1234567893",
            "email": "bob.brown@example.com"
        }           
]

   
        # Get the national_id from query parameters
        national_id = request.query_params.get('national_id', '').strip()

        if not national_id:
            return Response(
                {"success": False, "message": "National ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Search for the member with the given national ID
        member = next((m for m in MEMBERS if m["national_id"] == national_id), None)

        if member:
            return Response(
                {"success": True, "data": member},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"success": False, "message": "Member not found."},
                status=status.HTTP_404_NOT_FOUND
            )



# class EsewaRequestView(View):
#     def get(self,request,*args,**kwargs):
#         o_id=request.GET.get('o_id')
#         order= Order.objects.get(id=o_id)

#         cart_items = CartItem.objects.filter(user=request.user)
#         for item  in cart_items:
#             orderproduct = OrderProduct()
#             orderproduct.order_id= order.id
#             orderproduct.user_id = request.user.id
#             orderproduct.product_id = item.product_id
#             orderproduct.quantity = item.quantity
#             orderproduct.product_price = item.product.price
#             orderproduct.ordered = True
#             orderproduct.save() 
#             product = Product.objects.get(id=item.product_id)
#             product.save() 

#         context={"order":order}
#         return render(request,'esewarequest.html',context)


# class EsewaVerifyView(View):
    def get(self,request,*args,**kwargs):
        import xml.etree.ElementTree as ET
        oid=request.GET.get('oid')
        amt=request.GET.get('amt')
        refId=request.GET.get('refId')
        url ="https://uat.esewa.com.np/epay/transrec"
        d = {
            'amt': amt,
            'scd': 'epay_payment',
            'rid':refId ,
            'pid':oid,
        }
        resp = req.post(url, d)
        root = ET.fromstring(resp.content)
        status=root[0].text.strip()
        order_id=oid.split("_")[1]
        order_obj=Order.objects.get(id=order_id)
        if status == "Success":
            order_obj.is_ordered = True
            order_obj.save()
            cart = CartItem.objects.filter(user=request.user)
            cart.delete()
            return redirect('order_complete')
        else:
            order_obj.delete()
            messages.warning(request, 'Payment failed. Please try again.')
            return redirect('cart')