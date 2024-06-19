from .views import * 
from django.urls import path, include
from django.conf import settings

urlpatterns = [
    path('membership/card/<family_uuid>', PrintPdfSlipView.as_view(), name="print")
    # path('attach/', views.attach, name='attach')
]

if settings.DEBUG:
    urlpatterns += [
        path('membership-card/test', index, name='index'),
    ]