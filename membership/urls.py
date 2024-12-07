from .views import * 
from django.urls import path, include
from django.conf import settings
from .paypal_service import *
#from .views import CreateUserWithInsureeRoleView


urlpatterns = [
    path('membership/card/<insuree_uuid>', PrintPdfSlipView.as_view(), name="print"),
    # path('attach/', views.attach, name='attach')
]

if settings.DEBUG:
    urlpatterns += [
        path('membership-card/test', index, name='index'),
        path('login', Signin.as_view(), name='token_obtain_pair'),
        path("enrollment/", EnrollmentView.as_view(), name="EnrollmentSerializer"),
        path("insuree-information/", InsureeInformation.as_view(), name="InsureeInformation"),
        path("locations/", LocationAPIView.as_view(), name="LocationAPIView"),
        path("hospitals", HospitalAPIView.as_view(), name="HospitalAPIView"),
        path("config/", Config.as_view(), name="Config"),
    ]
    urlpatterns += [
        #path('create-insuree/', CreateUserWithInsureeRoleView.as_view(), name='create_user'),
        path('register/', RegisterAPIView.as_view(), name='register'),
        path('check-username/', UsernameExistsView.as_view(), name='check-username'),
        path('validate-otp/', ValidateOTPAPIView.as_view(), name='validate_otp'),
        path('resend-otp/', ResendOTPAPIView.as_view(), name='resend-otp'),
    ]
    #claims/ polices/ grievances ?
    urlpatterns += [
        #path('create-insuree/', CreateUserWithInsureeRoleView.as_view(), name='create_user'),
        path('claims/', InsureeClaimsApi.as_view(), name='claim-lists'),
        path('claimed-item-services/', InsureeClaimServiceItems.as_view(), name="claimed-item-services")
        #path('policies/', ValidateOTPAPIView.as_view(), name='validate_otp'),
    ] 
    urlpatterns += [
        path('fhir-patient/', PatientIdentifierAPIView.as_view(), name='PatientIdentifierAPIView'),
    ]

    #external route - calling third party system for interoperability

    urlpatterns+=[
        path('nationalId/', NationalIDView.as_view(), name="national-id")
    ]
    #nepali payment channel
    urlpatterns+=[

        # path('esewarequest/',EsewaRequestView.as_view(),name='esewarequest'),
        # path('esewa-verify/',EsewaVerifyView.as_view(),name='esewaverify'),
    ]
    #international payment channel example
    
    urlpatterns += [
        path("access-token/", GetAccessToken.as_view(), name="get_access_token"),
        path("create-payment/", CreatePayment.as_view(), name="create_payment"),
        path("execute-payment/", ExecutePayment.as_view(), name="execute_payment"),
    ]
