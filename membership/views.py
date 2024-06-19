

from wkhtmltopdf.views import PDFTemplateView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from django.http import  HttpResponse, HttpResponseForbidden
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.views import APIView
from membership.apps import MembershipCardConfig
from rest_framework.exceptions import ValidationError
from .services import PDFGenerationService
from django.shortcuts import render


class PrintPdfSlipView(APIView, PDFTemplateView):
    filename = MembershipCardConfig.membership_slip_name
    template_name = MembershipCardConfig.get_template_by_os()
    cmd_options = MembershipCardConfig.wkhtml_cmd_options_for_printing
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        if not request.user:
            return HttpResponseForbidden("You do not have permission to access this resource.")
        return super(PrintPdfSlipView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        family_uuid = request.GET.get('family_uuid')
        slip_type = request.GET.get('type')
        if not family_uuid:
            raise ValidationError("Missing 'family_uuid' parameter.")
        try:
            pdf_base64 = PDFGenerationService.generate_pdf(request.user, family_uuid, slip_type)
            response = Response({
                'pdf_base64': pdf_base64,
                'filename': self.filename,
                'content_type': 'application/pdf',
            })
            return response
        except Exception as e:
            return Response({'error': str(e)}, status=400)




def index(request):
    return render(request, 'test-card.html')


