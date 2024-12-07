
from rest_framework import serializers, viewsets, status
from insuree.models import Insuree, InsureePolicy, Family
from policy.models import Policy
from claim.models import Claim
from location import models as location_models
from datetime import datetime, timedelta

class SignInSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255, required=True)
    password = serializers.CharField(max_length=255, required=True, write_only=True)



class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = location_models.HealthFacility
        fields = "__all__"

# class PolicySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Policy
#         fields = "__all__"


class InsureePolicySerializer(serializers.ModelSerializer):
    policy_status = serializers.SerializerMethodField()
    class Meta:
        model = InsureePolicy
        fields = ['enrollment_date', 'start_date', 'effective_date', 'expiry_date', "policy_status"]
    
    def get_policy_status(self, obj):
        if obj.expiry_date:
            return 'Active' if obj.expiry_date >=datetime.now().today() else "Inctive"
        else:
            return ' NA'


class InsureeSerializer(serializers.ModelSerializer):
    # health_facility = HospitalSerializer()
    fullname = serializers.SerializerMethodField()
    date_of_birth = serializers.SerializerMethodField()
    insuree_gender = serializers.SerializerMethodField()
    first_service_point = serializers.SerializerMethodField()
    district_fsp  = serializers.SerializerMethodField()
    photo = serializers.SerializerMethodField()
    policy_status = serializers.SerializerMethodField()
    latest_policy = serializers.SerializerMethodField()
    class Meta:
        model = Insuree
        fields = ['fullname','chf_id', 'date_of_birth', 'insuree_gender', 'first_service_point', 'district_fsp', 'photo', 'policy_status', "latest_policy"]
        # fields = '__all__'
    
    def get_fullname(self, obj):
        return f"{obj.last_name} {obj.other_names}"

    def get_date_of_birth(self, obj):
        if obj.dob is None:
            return "Date of Birth: Not provided"
        
        dob = obj.dob if isinstance(obj.dob, datetime) else datetime.strptime(str(obj.dob), '%Y-%m-%d')
        age = (datetime.today() - dob).days // 365
        return f"{dob.date()} ({age})"


    def get_insuree_gender(self, obj):
        if obj.gender:
            return f"{obj.gender.gender}"
        else:
            return f"N/A"


    def get_first_service_point(self, obj):
        if obj.health_facility:
            return f"{obj.health_facility.name if obj.health_facility else 'Not Assigned'}"
        else:
            return f"HF not Assigned"

    def get_district_fsp(self, obj):
        if obj.health_facility:
            if obj.health_facility.location:
                return f"{obj.health_facility.location.name if obj.health_facility.location else 'Not Assigned'}"
        else:
            return f"HF address not Assigned"
    
    def get_photo(self, obj):
        return f"""https://qph.cf2.quoracdn.net/main-thumb-145284757-200-uotzltsmkidnmdkcyshgrobwujmlhogo.jpeg"""
    def get_policy_status(self, obj):
        insuree_policy = InsureePolicy.objects.filter(insuree=obj, validity_to=None).first()
        if insuree_policy:
            return f"{'Active' if insuree_policy.expiry_date <=datetime.now().today() else 'Expired'}"
        else:
            return f"Policy Not Found"
    
    def get_latest_policy(self, obj):
        insuree_policy = InsureePolicy.objects.filter(insuree=obj, validity_to=None).first()
        return InsureePolicySerializer(insuree_policy).data if insuree_policy else None

    
class FamilySerializer(serializers.ModelSerializer):
    members = serializers.SerializerMethodField()
    class Meta:
        model = Family
        fields = ['members']

    def get_members(self, obj):
        family_members = Insuree.objects.filter(family=obj, validity_to=None)
        return InsureeSerializer(family_members, many=True).data



class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = location_models.Location
        fields = "__all__"

class ClaimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Claim
        fields = '__all__'


class UserRegistrationSerializer(serializers.Serializer):
    chfid = serializers.CharField(max_length=50)  # Insuree ID
    head_chfid = serializers.CharField(max_length=50)  # Head Insuree ID
    dob = serializers.DateField()  # Date of Birth (YYYY-MM-DD)
    phone = serializers.CharField(max_length=15, required=False)  # Optional phone
    email = serializers.EmailField(required=False)  # Optional email

class OTPValidationSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)