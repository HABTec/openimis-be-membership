import graphene
from .services import PDFGenerationService  
class GeneratePdfSlip(graphene.Mutation):
    class Arguments:
        insuree_uuid = graphene.String(required=True)
        slip_type = graphene.String(required=False)

    base64_pdf = graphene.String()

    def mutate(self, info, insuree_uuid, slip_type=None):
        user = getattr(getattr(info, "context", None), "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            raise Exception("You do not have permission to access this resource.")
        pdf_base64 = PDFGenerationService.generate_pdf(user, insuree_uuid, slip_type)
        return GeneratePdfSlip(base64_pdf=pdf_base64)
