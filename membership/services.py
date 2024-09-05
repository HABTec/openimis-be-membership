

from insuree.models import Insuree,Family, InsureePolicy
from membership.apps import MembershipCardConfig
import base64
from wkhtmltopdf.views import PDFTemplateResponse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.http import HttpRequest
from django.utils.safestring import mark_safe
import calendar
from datetime import datetime, timedelta
from django.conf import settings

from datetime import datetime
from insuree.models import Insuree, Family, InsureePhoto, FamilyType, ConfirmationType
from location import models as location_models
# from your_app.models import FamilyType, ConfirmationType
from django.shortcuts import get_object_or_404
import base64
from django.core.files.base import ContentFile




class PDFGenerationService:
    @staticmethod
    def generate_pdf(user, insuree_uuid, slip_type=None):
        insuree = Insuree.objects.filter(uuid=insuree_uuid, validity_to=None)
        insuree_families = Insuree.objects.filter(family=insuree.first().family).order_by("id").all()
        if  not insuree:
            raise Exception("Insuree not found.")
        chfid = str(insuree.first().chf_id)
        chfid_array = list(chfid)
        photo = PDFGenerationService.get_insuree_photo(insuree.first())
        current_year_html = PDFGenerationService.generate_eligibility_html(insuree, datetime.now().year)
        next_year_html = PDFGenerationService.generate_eligibility_html(insuree, datetime.now().year + 1)

        context = {
            "insurees": insuree_families,
            "insuree": insuree.first(),
            "chfid_array": chfid_array,
            "multiple" : False, #Multiple Card
            "title": f"{insuree.first().last_name} {insuree.first().other_names}",
            "current_year_html": current_year_html,  # Adding the current year HTML to the context
            "next_year_html": next_year_html,  # Adding the next year HTML to the context
            "conditions" : MembershipCardConfig.get_terms_and_conditions
        }
        # Prepare an HttpRequest object
        request = HttpRequest()
        request.user = user
        # Create a PDF response
        if not MembershipCardConfig.get_template_by_os():
            raise Exception("Template for printing not available")
        response = PDFTemplateResponse(
            request=request,
            template=MembershipCardConfig.get_template_by_os(),
            context=context,
            cmd_options=MembershipCardConfig.wkhtml_cmd_options_for_printing,
            filename=MembershipCardConfig.membership_slip_name,
        )
        response.render()
        pdf_content = response.content
        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        return pdf_base64
    
    @staticmethod
    def get_insuree_photo(insuree):
        if insuree and insuree.photos.exists():
            insuree_photo = insuree.photos.first() 
            return insuree_photo.full_file_path()
        return None

    @staticmethod
    def generate_eligibility_html(insuree, year):
        # import pdb;pdb.set_trace();
        insuree_policies = InsureePolicy.objects.filter(insuree=insuree.first())
        
        month_names = [calendar.month_name[i] for i in range(1, 13)]
        month_divs = {month: '<div style="border: solid 1px rgb(1, 1, 1); width: 100px;height: 100px; border-radius: 50%;"></div>' for month in month_names}

        for policy in insuree_policies:
            start_date = policy.validity_from.date() if isinstance(policy.validity_from, datetime) else policy.validity_from
            end_date = policy.validity_to.date() if policy.validity_to else datetime.now().date()
            end_date = end_date if isinstance(end_date, datetime) else datetime.combine(end_date, datetime.min.time())
            
            while start_date <= end_date.date():
                if start_date.year == year:
                    month_name = calendar.month_name[start_date.month]
                    month_divs[month_name] = f'<div style="border: solid 1px rgb(1, 1, 1); width: 100px;height: 100px; border-radius: 50%; opacity: 0.3; background-image: url(\'https://release.openimis.org/front/static/media/openIMIS.f3351d9a.png\'); background-size: cover;"></div>'
                start_date = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1)

        eligibility_html = f'<table style="width: 100%;" border="1"><thead><tr><th colspan="3">{year}</th></tr></thead><tbody>'
        month_divs_list = list(month_divs.values())

        for i in range(0, len(month_divs_list), 3):
            eligibility_html += '<tr>'
            for j in range(3):
                if i + j < len(month_divs_list):
                    eligibility_html += f'<td>{month_divs_list[i + j]}</td>'
                else:
                    eligibility_html += '<td></td>'
            eligibility_html += '</tr>'
        
        eligibility_html += '</tbody></table>'
        return eligibility_html


def generate_conditions_html(conditions):
    conditions_html = '<ol type="1">'
    for condition in conditions:
        conditions_html += f'<li>{condition}</li>'
    conditions_html += '</ol>'
    return conditions_html



def send_email(to_email, subject, context, text_template, html_template, attachments=[]):
    try:
        plaintext = get_template(text_template)
        text_body = plaintext.render(context)

        html_body = None
        if html_template:
            html = get_template(html_template)
            html_body = html.render(context)

        recipients = [to_email]
        msg = EmailMultiAlternatives(subject, text_body, to=recipients,
                                     reply_to=settings.REPLY_TO)
        if html_body:
            msg.attach_alternative(html_body, "text/html")

        for filename, content, mimetype in attachments:
            msg.attach(filename, content, mimetype)

        msg.send()
    except Exception as e:
        print(e)
    return True








def create_insuree(data, family=None):
    """
    Creates an Insuree instance and returns it.
    """
    insuree = Insuree.objects.create(
        chf_id=data.get("chfid"),
        last_name=data.get("lastName", ""),
        other_names=data.get("givenName", ""),
        phone=data.get("phone"),
        dob=data.get("birthdate"),
        email=data.get("email"),
        head=True,
        card_issued=False,
        audit_user_id=-1,
        family=family,
    )
    return insuree


def create_family(data, head_insuree):
    """
    Creates a Family instance and returns it.
    """
    # family_type = get_object_or_404(FamilyType, name=data.get('familyType'))
    # confirmation_type = get_object_or_404(ConfirmationType, name=data.get('confirmationType'))
    
    family = Family.objects.create(
        head_insuree=head_insuree,
        location=location_models.Location.objects.filter(id=int(data.get("healthFacility")), validity_to=None).first(),  # Adjust as needed
        poverty=data.get("poverty", False),
        family_type=FamilyType.objects.filter(code="C").first(),
        address=data.get("addressDetail", ""),
        confirmation_no=data.get("confirmationNumber", ""),
        confirmation_type=ConfirmationType.objects.filter(code="A").first(),
        audit_user_id=-1,
    )
    return family


def base64_to_file(base64_string, file_name):
    if ';base64,' in base64_string:
        format, imgstr = base64_string.split(';base64,')
        ext = format.split('/')[-1]
    else:
        imgstr = base64_string
        ext = 'jpg'  # Default to jpg if the format is not specified

    return ContentFile(base64.b64decode(imgstr), name=f"{file_name}.{ext}")

def create_insuree_photo(insuree, photo_data, user, now):
    """
    Creates an InsureePhoto instance and associates it with the given Insuree.
    """
    from insuree.services import handle_insuree_photo
    
    # Convert base64 string to Django file
    photo_file = base64_to_file(photo_data, insuree.chf_id)
    
    # Extract the binary data from the ContentFile object
    photo_binary_data = photo_file.read()
    
    # Prepare the data dictionary with the binary photo data
    data = {
        'photo': photo_binary_data,  # Binary data extracted from the ContentFile
        'officer_id' : 1,
        'date' : now.today()
    }
    
    # Call handle_insuree_photo with the prepared data
    handle_insuree_photo(user, now, insuree, data)
    