
import graphene
from .services import PDFGenerationService  # Adjust the import based on your project structure

class GeneratePdfSlip(graphene.Mutation):
    class Arguments:
        insuree_uuid = graphene.String(required=True)
        slip_type = graphene.String(required=False)

    base64_pdf = graphene.String()

    def mutate(self, info, insuree_uuid, slip_type=None):
        user = info.context.user
        # if not user.is_authenticated:
        #     raise Exception("You do not have permission to access this resource.")
        
        pdf_base64 = PDFGenerationService.generate_pdf(user, insuree_uuid, slip_type)
        return GeneratePdfSlip(base64_pdf=pdf_base64)