
import graphene


from .gql_mutations import GeneratePdfSlip

class Query(graphene.ObjectType):
    pass


class Mutation(graphene.ObjectType):
    generate_pdf_slip = GeneratePdfSlip.Field()
