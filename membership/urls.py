from .views import * 
from django.urls import path, include
from django.conf import settings

urlpatterns = [
    path('membership/card/<insuree_uuid>', PrintPdfSlipView.as_view(), name="print"),
    path('create/insuree', CreateInsureeUser.as_view(), name="create_insuree"),
    # path('attach/', views.attach, name='attach')
]

if settings.DEBUG:
    urlpatterns += [
        path('membership-card/test', index, name='index'),
        path('login', signin.as_view(), name='token_obtain_pair'),
        path("enrollment/", EnrollmentView.as_view(), name="EnrollmentSerializer"),
        path("insuree-information/", InsureeInformation.as_view(), name="InsureeInformation"),
        path("locations/", LocationAPIView.as_view(), name="LocationAPIView"),
        path("hospitals", HospitalAPIView.as_view(), name="HospitalAPIView"),
        path("config/", Config.as_view(), name="Config")
    ]