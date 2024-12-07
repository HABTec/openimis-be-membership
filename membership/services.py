from insuree.models import Insuree, Family, InsureePolicy
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
import json
from datetime import datetime
from insuree.models import (
    Insuree,
    Family,
    InsureePhoto,
    FamilyType,
    ConfirmationType,
    Gender,
    Relation,
    InsureeStatus,
)
from contribution.models import Premium, PayTypeChoices, Payer
from location import models as location_models
from policy.models import Policy
from django.shortcuts import get_object_or_404
import base64
from django.core.files.base import ContentFile


class PDFGenerationService:
    @staticmethod
    def generate_pdf(user, insuree_uuid, slip_type=None):
        insuree = Insuree.objects.filter(uuid=insuree_uuid, validity_to=None)
        insuree_families = (
            Insuree.objects.filter(family=insuree.first().family).order_by("id").all()
        )
        if not insuree:
            raise Exception("Insuree not found.")
        chfid = str(insuree.first().chf_id)
        chfid_array = list(chfid)
        photo = PDFGenerationService.get_insuree_photo(insuree.first())
        current_year_html = PDFGenerationService.generate_eligibility_html(
            insuree, datetime.now().year
        )
        next_year_html = PDFGenerationService.generate_eligibility_html(
            insuree, datetime.now().year + 1
        )

        context = {
            "insurees": insuree_families,
            "insuree": insuree.first(),
            "chfid_array": chfid_array,
            "multiple": False,  # Multiple Card
            "title": f"{insuree.first().last_name} {insuree.first().other_names}",
            "current_year_html": current_year_html,  # Adding the current year HTML to the context
            "next_year_html": next_year_html,  # Adding the next year HTML to the context
            "conditions": MembershipCardConfig.get_terms_and_conditions,
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
        pdf_base64 = base64.b64encode(pdf_content).decode("utf-8")
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
        month_divs = {
            month: '<div style="border: solid 1px rgb(1, 1, 1); width: 100px;height: 100px; border-radius: 50%;"></div>'
            for month in month_names
        }

        for policy in insuree_policies:
            start_date = (
                policy.validity_from.date()
                if isinstance(policy.validity_from, datetime)
                else policy.validity_from
            )
            end_date = (
                policy.validity_to.date()
                if policy.validity_to
                else datetime.now().date()
            )
            end_date = (
                end_date
                if isinstance(end_date, datetime)
                else datetime.combine(end_date, datetime.min.time())
            )

            while start_date <= end_date.date():
                if start_date.year == year:
                    month_name = calendar.month_name[start_date.month]
                    month_divs[month_name] = (
                        f"<div style=\"border: solid 1px rgb(1, 1, 1); width: 100px;height: 100px; border-radius: 50%; opacity: 0.3; background-image: url('https://release.openimis.org/front/static/media/openIMIS.f3351d9a.png'); background-size: cover;\"></div>"
                    )
                start_date = (start_date.replace(day=28) + timedelta(days=4)).replace(
                    day=1
                )

        eligibility_html = f'<table style="width: 100%;" border="1"><thead><tr><th colspan="3">{year}</th></tr></thead><tbody>'
        month_divs_list = list(month_divs.values())

        for i in range(0, len(month_divs_list), 3):
            eligibility_html += "<tr>"
            for j in range(3):
                if i + j < len(month_divs_list):
                    eligibility_html += f"<td>{month_divs_list[i + j]}</td>"
                else:
                    eligibility_html += "<td></td>"
            eligibility_html += "</tr>"

        eligibility_html += "</tbody></table>"
        return eligibility_html


def generate_conditions_html(conditions):
    conditions_html = '<ol type="1">'
    for condition in conditions:
        conditions_html += f"<li>{condition}</li>"
    conditions_html += "</ol>"
    return conditions_html


def send_email(
    to_email, subject, context, text_template, html_template, attachments=[]
):
    try:
        plaintext = get_template(text_template)
        text_body = plaintext.render(context)

        html_body = None
        if html_template:
            html = get_template(html_template)
            html_body = html.render(context)

        recipients = [to_email]
        msg = EmailMultiAlternatives(
            subject, text_body, to=recipients, reply_to=settings.REPLY_TO
        )
        if html_body:
            msg.attach_alternative(html_body, "text/html")

        for filename, content, mimetype in attachments:
            msg.attach(filename, content, mimetype)

        msg.send()
    except Exception as e:
        print(e)
    return True


def get_gender(data):
    if data is not None:
        if data.lower() == "male":
            return Gender.objects.filter(code="M").first()
        else:
            return Gender.objects.filter(code="F").first()
    return None


def get_relationship(data):
    relation = None
    if data:
        relation = Relation.objects.filter(relation=data).first()
    return relation


def create_insuree_and_family(request):
    """
    Creates Insuree instances for all members and attaches them to the same Family instance.
    """
    members = request.data.get("members")
    family_data = request.data.get("family")

    # Step 1: Find the head member (with isHead: 1)
    head_member = None
    for member in members:
        json_content = json.loads(member["json_content"])
        if json_content.get("isHead") == 1:
            head_member = member
            break

    if not head_member:
        raise ValueError("No head member found with isHead: 1.")

    # Step 2: Create the head Insuree (pass request.user)
    head_insuree = create_insuree(head_member, family=None, user=request.user)

    # Step 3: Create the family with the head Insuree
    family = create_family(family_data, head_insuree)

    # Step 4: Create the remaining members (excluding the head)
    for member in members:
        if member != head_member:
            create_insuree(member, family, user=request.user)  # Pass request.user

    return head_insuree


def create_insuree(member, family=None, user=None):
    """
    Creates a single Insuree instance. If family is provided, associates the Insuree with the family.
    """
    # import pdb

    # pdb.set_trace()
    print("member", member.pop('photo'))
    # Handle case when json_content is None
    json_content = {}
    if member.get("json_content"):
        try:
            json_content = json.loads(member["json_content"])
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Error decoding JSON content: {e}. Skipping this member.")
            return None  # Skip this member if JSON is invalid or None

    # Prepare data for Insuree creation
    insuree_data = {
        "chf_id": member.get("chfid"),
        "head": json_content.get("isHead", 0),
        "phone": json_content.get("phone"),
        "dob": json_content.get("birthdate"),
        "email": json_content.get("email"),
        "gender": get_gender(json_content.get("gender")),
        "other_names": json_content.get("givenName") if json_content.get("givenName") else "",
        "last_name": json_content.get("lastName") if json_content.get("lastName") else "",
        "marital": "",  # Default value since it's not provided
        "photo": None,
        "health_facility_id": json_content.get("healthFacility"),
        "relationship": get_relationship(json_content.get("relationShip")),
        "status": InsureeStatus.ACTIVE,
        "status_reason": None,
        "audit_user_id": -1,
        "card_issued": False,
        "family": family,  # Attach family if provided
    }

    # Create the Insuree instance
    insuree = Insuree.objects.create(**insuree_data)

    # Handle photo if present
    if member.get("photo"):
        insuree.photo = create_insuree_photo(
            user, datetime.now(), insuree, member.get("photo")
        )

    return insuree


def create_insuree_photo(user, now, insuree, photo_data):
    """
    Creates an InsureePhoto instance and associates it with the given Insuree.
    """
    from insuree.services import handle_insuree_photo

    # Convert base64 string to Django file
    photo_file = base64_to_file(photo_data, insuree.chf_id)
    photo_binary_data = photo_file.read()

    # Prepare data for photo handling
    data = {
        "photo": photo_binary_data,
        "officer_id": 1,
        # 'id_for_audit': -1,
        "date": now.today(),
    }

    # Check if user is not None before assigning
    # if hasattr(user, 'id_for_audit'):
    #     user.id_for_audit = -1
    #     user.save()

    # Handle insuree photo
    return handle_insuree_photo(user, now, insuree, data)


def create_family(data, head_insuree):
    """
    Creates a Family instance and returns it using the parsed json_content data.
    """
    # Parse the json_content field
    json_content = json.loads(data["json_content"])

    # Fetch related fields (if needed) from other models
    family_type = FamilyType.objects.filter(code=json_content.get("familyType")).first()
    confirmation_type = ConfirmationType.objects.filter(
        code=json_content.get("confirmationType")
    ).first()

    # Create the family instance
    family = Family.objects.create(
        head_insuree=head_insuree,
        location=None,  # Adjust location logic as necessary
        poverty=data.get("poverty", False),
        family_type=family_type,
        address=json_content.get("addressDetail", ""),
        confirmation_no=json_content.get("confirmationNumber", ""),
        confirmation_type=confirmation_type,
        audit_user_id=-1,
    )

    return family


def create_insuree_policy(insuree):
    insuree_policy = InsureePolicy.objects.create(
        insuree=insuree,
        policy=Policy.objects.first(),
        start_date=datetime.now(),
        enrollment_date=datetime.now(),
        expiry_date=datetime.now() + timedelta(days=365),
        effective_date=datetime.now(),
        audit_user_id=-1,
    )
    return insuree_policy


def create_contribution(
    insuree_policy,
    receipt="None",
    amount=700.0 * 5,
    payer=None,
    is_photo_fee=False,
    is_offline=False,
    audit_user_id=-1,
):
    """
    Creates a Premium instance with the given parameters.

    Args:
        policy: The policy associated with this premium.
        receipt: The receipt string associated with the payment.
        amount: The amount of the premium (default is 1.0).
        payer: An instance of Payer or None (default is None).
        is_photo_fee: Boolean indicating if this is a photo fee (default is False).
        is_offline: Boolean indicating if this is an offline payment (default is False).
        audit_user_id: ID of the user making the audit (default is -1).
    """
    # Fetch or create a default Payer instance if not provided
    if payer is None:
        payer = Payer.objects.first()  # Any

    # Create the Premium object
    Premium.objects.create(
        policy=insuree_policy.policy,
        payer=payer,  # Set the payer object
        amount=amount,
        receipt=receipt,
        pay_date=datetime.now(),  # Using the current date and time for payment
        pay_type=PayTypeChoices.BANK_TRANSFER,  # Using Bank Transfer as the payment type
        is_photo_fee=is_photo_fee,  # Set photo fee status
        is_offline=is_offline,  # Set offline status
        reporting_id=None,  # Adjust this as necessary
        reporting_commission_id=None,  # Adjust this as necessary
        overview_commission_report=None,  # Adjust this as necessary
        all_details_commission_report=None,  # Adjust this as necessary
        source=None,  # Adjust this as necessary
        source_version=None,  # Adjust this as necessary
        audit_user_id=audit_user_id,  # Use the provided audit user ID
        created_date=datetime.now(),  # Set created date to now
    )


def base64_to_file(base64_string, file_name):
    if ";base64," in base64_string:
        format, imgstr = base64_string.split(";base64,")
        ext = format.split("/")[-1]
    else:
        imgstr = base64_string
        ext = "jpg"  # Default to jpg if the format is not specified

    return ContentFile(base64.b64decode(imgstr), name=f"{file_name}.{ext}")
