
import graphene
from graphene_django import DjangoObjectType
from .models import Membership, MembershipType, AreaType
from .gql_mutations import GeneratePdfSlip
from datetime import date


class MembershipTypeNode(DjangoObjectType):
    class Meta:
        model = MembershipType
        fields = '__all__'
    
    payment_amount = graphene.Float(level_number=graphene.Int(required=True))
    
    def resolve_payment_amount(self, info, level_number):
        return self.get_payment_amount(level_number - 1)  # Convert to 0-based index


class MembershipNode(DjangoObjectType):
    class Meta:
        model = Membership
        fields = '__all__'
    
    payment_amount = graphene.Float()
    
    def resolve_payment_amount(self, info):
        return self.get_payment_amount()


class MembershipInput(graphene.InputObjectType):
    id = graphene.ID(required=False)
    member_name = graphene.String(required=True)
    member_id = graphene.String(required=True)
    membership_type_id = graphene.ID(required=True)
    level = graphene.Int(required=True)
    start_date = graphene.Date(required=True)
    end_date = graphene.Date(required=True)
    status = graphene.String(required=True)


class MembershipTypeInput(graphene.InputObjectType):
    id = graphene.ID(required=False)
    region = graphene.String(required=True)
    area_type = graphene.String(required=True)
    levels_config = graphene.JSONString(required=True)
    payments = graphene.List(graphene.Float, required=True)
    is_paying = graphene.Boolean(required=True, default_value=True)


class CreateOrUpdateMembership(graphene.Mutation):
    class Arguments:
        data = MembershipInput(required=True)
    
    membership = graphene.Field(MembershipNode)
    success = graphene.Boolean()
    message = graphene.String()
    
    @classmethod
    def mutate(cls, root, info, data):
        try:
            membership_data = {
                'member_name': data.member_name,
                'member_id': data.member_id,
                'membership_type_id': data.membership_type_id,
                'level': data.level,
                'start_date': data.start_date,
                'end_date': data.end_date,
                'status': data.status,
            }
            
            if hasattr(data, 'id') and data.id:
                # Update existing membership
                membership = Membership.objects.get(id=data.id)
                for key, value in membership_data.items():
                    setattr(membership, key, value)
                membership.save()
                message = "Membership updated successfully"
            else:
                # Create new membership
                membership = Membership.objects.create(**membership_data)
                message = "Membership created successfully"
            
            return CreateOrUpdateMembership(
                membership=membership,
                success=True,
                message=message
            )
        except Exception as e:
            return CreateOrUpdateMembership(
                membership=None,
                success=False,
                message=str(e)
            )


class CreateOrUpdateMembershipType(graphene.Mutation):
    class Arguments:
        data = MembershipTypeInput(required=True)
    
    membership_type = graphene.Field(MembershipTypeNode)
    success = graphene.Boolean()
    message = graphene.String()
    
    @classmethod
    def mutate(cls, root, info, data):
        try:
            if hasattr(data, 'id') and data.id:
                # Update existing membership type
                membership_type = MembershipType.objects.get(id=data.id)
                membership_type.region = data.region
                membership_type.area_type = data.area_type
                membership_type.levels_config = data.levels_config
                membership_type.payments = data.payments
                membership_type.is_paying = data.is_paying
                membership_type.save()
                message = "Membership type updated successfully"
            else:
                # Create new membership type
                membership_type = MembershipType.objects.create(
                    region=data.region,
                    area_type=data.area_type,
                    levels_config=data.levels_config,
                    payments=data.payments,
                    is_paying=data.is_paying
                )
                message = "Membership type created successfully"
            
            return CreateOrUpdateMembershipType(
                membership_type=membership_type,
                success=True,
                message=message
            )
        except Exception as e:
            return CreateOrUpdateMembershipType(
                membership_type=None,
                success=False,
                message=str(e)
            )


class Query(graphene.ObjectType):
    all_memberships = graphene.List(MembershipNode)
    membership = graphene.Field(MembershipNode, id=graphene.ID())
    all_membership_types = graphene.List(MembershipTypeNode, region=graphene.String(), area_type=graphene.String())
    membership_type = graphene.Field(MembershipTypeNode, id=graphene.ID())
    get_membership_payment = graphene.Float(
        region=graphene.String(required=True),
        area_type=graphene.String(required=True),
        level_number=graphene.Int(required=True)
    )
    
    def resolve_all_memberships(self, info, **kwargs):
        return Membership.objects.all()
    
    def resolve_membership(self, info, id):
        return Membership.objects.get(id=id)
    
    def resolve_all_membership_types(self, info, region=None, area_type=None, **kwargs):
        qs = MembershipType.objects.all()
        if region:
            qs = qs.filter(region__iexact=region)
        if area_type:
            qs = qs.filter(area_type__iexact=area_type)
        return qs
    
    def resolve_membership_type(self, info, id):
        return MembershipType.objects.get(id=id)
    
    def resolve_get_membership_payment(self, info, region, area_type, level_number):
        return MembershipType.get_membership_payment(region, area_type, level_number)


class Mutation(graphene.ObjectType):
    create_or_update_membership = CreateOrUpdateMembership.Field()
    create_or_update_membership_type = CreateOrUpdateMembershipType.Field()
    generate_pdf_slip = GeneratePdfSlip.Field()
