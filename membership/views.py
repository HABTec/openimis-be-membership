from datetime import datetime, timedelta

from django.contrib.auth import authenticate
from django.db import transaction
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework import  status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from insuree.models import Family, Insuree, InsureePhoto, InsureePolicy
from location import models as location_models

from membership.apps import MembershipCardConfig
from membership.utils.generic_response_utils import error_response, success_response

from .services import PDFGenerationService, create_family, create_insuree, create_insuree_photo
from core.schema import update_or_create_user
from wkhtmltopdf.views import PDFTemplateView


from .serializers import (
    SignInSerializer,
    # PolicySerializer,
    InsureeSerializer,
    FamilySerializer,
    LocationSerializer,
    HospitalSerializer,
    InsureePolicySerializer,
)



class CreateInsureeUser(APIView):
    def post(self, request):
        chfid = request.data.get('chfid')
        head_chfid = request.data.get('headChfid')
        dob = request.data.get('dob')
        mobile = request.data.get('mobile')
        password = request.data.get('password')
        
        insuree = get_object_or_404(Insuree, chf_id=chfid)
        is_head = get_object_or_404(Insuree, chf_id=head_chfid)
        
        if insuree.dob != dob:
            return error_response('Invalid Head and insuree or dob, please check your insurance no')
        
        # data = {
        #     "uuid": None,
        #     "username": mobile,
        #     "user_types": ["INTERACTIVE"],
        #     "last_name": insuree.last_name,
        #     "other_names": insuree.other_names,
        #     "phone": mobile,
        #     "email": insuree.email,
        #     "password": password,
        #     "health_facility_id": insuree.health_facility.pk,
        #     "districts": [],
        #     "location_id": None,
        #     "language": "en",
        #     "roles": ["10"],
        #     "substitution_officer_id": None,
        #     "village_ids": [],
        # }
        # create_user = update_or_create_user(data, request.user)
        return Response({'success': True})
            


class VerifyOtp(APIView):
    def post(self, request):
        otp = request.data.get('otp')
        if not otp=='123456':
            return error_response('Invalid OTP')
        chfid="1212121212" #otp.insuree
        mobile='9849298499' #otp.mobile,
        password='1onepiece' #otp.password
        insuree=Insuree.objects.filter(chf_if=chfid, validity_to=None).first()
        data = {
            "uuid": None,
            "username": mobile,
            "user_types": ["INTERACTIVE"],
            "last_name": insuree.last_name,
            "other_names": insuree.other_names,
            "phone": mobile,
            "email": insuree.email,
            "password": password,
            "health_facility_id": insuree.health_facility.pk,
            "districts": [],
            "location_id": None,
            "language": "en",
            "roles": ["10"],
            "substitution_officer_id": None,
            "village_ids": [],
        }
        create_user = update_or_create_user(data, request.user)
        #otp.delete()
        return Response({'success': True})
    
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
    permission_classes = ()

    def get(self, request):
        CONFIG = {
            "app_version": "1.0.0",
            "api_base_url": "https://api.your.domain.com",
            "support_email": "info@tinker.com.np",
            "develop_by" : "Tinker technologies",
            "supported_partners" : [
                {"name": "openIMIS", "logo": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTn8JOjtdC6rYuak2CJ3tcNJvlPiHKmNOtdrQ&s"},
                {"name": "AeHIN", "logo": "https://www.asiaehealthinformationnetwork.org/wp-content/uploads/2020/12/web_logo_default.png"},
                {"name": "Health Insurance Board Nepal", "logo": "https://hib.gov.np/site/img/shs.png"},
                ],
            "languages": {
                "fr_FR": {
                    "selected_language": "Fr",
                    "greeting": "Bonjour",
                    "enrollment": "Inscription",
                    "theme": "Thème",
                    "openimis": "openIMIS",
                    "poverty_status": "Statut de Pauvreté",
                    "search": "Recherche",
                    "policy": "Politique",
                    "search_for_insuree": "Rechercher un assuré...",
                    "new_enrollment": "Nouvelle Inscription",
                    "head": "Titulaire",
                    "head_chfid_is_required": "Le CHFID du titulaire est requis",
                    "head_chfid": "CHFID du Titulaire",
                    "last_name": "Nom de Famille",
                    "given_name": "Prénom",
                    "phone": "Téléphone",
                    "chfid": "CHFID",
                    "offline_enrollment": "Offline Enrollment",
                    "search_instruction" : "Tapez votre identifiant de membre ou scannez avec le code QR",
                    "logout_message" : "You are about to logout"
                },
                "en_US": {
                    "selected_language": "En",
                    "greeting": "Hello",
                    "enrollment": "Enrollment",
                    "theme": "Theme",
                    "openimis": "openIMIS",
                    "poverty_status": "Poverty Status",
                    "search": "Search",
                    "enrollment": "Enrollment",
                    "policy": "Policy",
                    "search_for_insuree": "Search for Insuree...",
                    "new_enrollment": "New Enrollment",
                    "head": "Head",
                    "head_chfid_is_required": "Head CHFID is required",
                    "head_chfid": "Head Chfid",
                    "last_name": "Last Name",
                    "given_name": "Given Name",
                    "phone": "Phone",
                    "chfid": "CHFID",
                    "offline_enrollment": "Offline Enrollment",
                    "search_instruction" : "Type your membership ID or scan with QR code",
                    "logout_message" : "Vous êtes sur le point de vous déconnecter"
                },
                "np_NP": {
                    "selected_language": "NP",
                    "greeting": "Hello",
                    "enrollment": "Enrollment",
                    "theme": "Theme",
                    "openimis": "openIMIS",
                    "poverty_status": "Poverty Status",
                    "search": "खोजी",
                    "enrollment": "भर्ना",
                    "policy": "नीति",
                    "search_for_insuree": "विमित खोजी गर्नुहोस...",
                    "new_enrollment": "नयाँ दर्ता",
                    "head": "प्रमुख",
                    "head_chfid_is_required": "घरमुलिको विमित नं अनिवार्य छ",
                    "head_chfid": "घरमुलिको विमित नं",
                    "last_name": "नाम",
                    "given_name": "थर",
                    "phone": "फोन",
                    "chfid": "विमित नं",
                    "offline_enrollment": "अफलाईन फर्ना विवरण",
                    "search_instruction" : "बीमा नं अथवा QR कोड स्क्यान गर्नुहोस",
                    "logout_message" : "लगआउट गर्दैहुनुहुन्छ ?"
                },
                "lo_LA": {
                    "selected_language": "ພາສາລາວ",
                    "greeting": "ສະບາຍດີ",
                    "enrollment": "ລົງທະບຽນ",
                    "theme": "ຫົວຂໍ້",
                    "openimis": "openIMIS",
                    "poverty_status": "ສະຖານະຍາກຈົນ",
                    "search": "ຄົ້ນຫາ",
                    "policy": "ນະໂຍບາຍ",
                    "search_for_insuree": "ຄົ້ນຫາຜູ້ໄດ້ຮັບປະກັນ...",
                    "new_enrollment": "ລົງທະບຽນໃຫມ່",
                    "head": "ຫົວໜ້າ",
                    "head_chfid_is_required": "ຕ້ອງການເລກປະຈໍາຕົວ CHFID ຂອງຫົວໜ້າ",
                    "head_chfid": "ເລກປະຈໍາຕົວ CHFID ຂອງຫົວໜ້າ",
                    "last_name": "ນາມສະກຸນ",
                    "given_name": "ຊື່",
                    "phone": "ໂທລະສັບ",
                    "chfid": "CHFID",
                    "offline_enrollment": "ລົງທະບຽນແບບອອບລາຍ",
                    "search_instruction" : "ພິມເລກປະຈໍາຕົວຂອງທ່ານ ຫຼື ສະແກນດ້ວຍລະຫັດ QR",
                    "logout_message" : "ທ່ານກຳລັງຈະອອກຈາກລະບົບ"
                }
            },
        }
        return Response(CONFIG)


class signin(APIView):
    permission_classes = ()
    authentication_classes = ()

    def post(self, request):
        received_json_data = request.data
        print("received_json_data", received_json_data)
        serializer = SignInSerializer(data=received_json_data)
        if False and not (
            received_json_data.get("ea_code") and received_json_data.get("birthday")
        ):
            return JsonResponse({"message": "Unauthenticated"}, status=400)
        from core.models import User, Role

        user = User.objects.filter(username=received_json_data.get("username")).first()
        # role = Role.objects.filter(id=user._u.role_id).first()
        # if not user.is_officer:
        #     return JsonResponse({'message':"Unauthenticated"}, status=400)
        if serializer.is_valid():
            user = authenticate(
                request,
                username=received_json_data["username"],
                password=received_json_data["password"],
            )
            if user is not None:
                refresh = RefreshToken.for_user(user)
                return JsonResponse(
                    {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                        "username": user.username,
                        "user": None,
                        "exp": refresh["exp"],
                        "first_name": user._u.other_names if user._u else "",
                        "last_name": user._u.last_name if user._u else "",
                        "email": user._u.email if user._u.email else "",
                        "user_type": user._u.user_type if user._u.email else "",
                    },
                    status=200,
                )
            else:
                return JsonResponse(
                    {
                        "message": "invalid username or password",
                    },
                    status=403,
                )
        else:
            return JsonResponse({"message": serializer.errors}, status=400)


class EnrollmentView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        print("request", request.data)
        if Insuree.objects.filter(
            chf_id=request.data.get("chfid"), validity_to=None
        ).exists():
            return error_response(message="Insuree with this CHF ID already exists.")
        head_insuree = Insuree.objects.filter(
            chf_id=request.data.get("headChfid"), validity_to=None
        ).first()
        is_new_enrolment = request.data.get("newEnrollment", False)
        if is_new_enrolment:
            insuree = create_insuree(request.data)
            family = create_family(request.data, insuree)
        else:
            insuree = create_insuree(request.data, head_insuree)

        if request.data.get("photo"):
            create_insuree_photo(
                insuree, request.data.get("photo"), request.user, datetime.now()
            )

        return Response({"Success": True}, status=status.HTTP_201_CREATED)


class PolicyCreateAndUpdateAPIView(APIView):
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
    permission_classes = [IsAuthenticated]
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

    def get(self, request):
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
