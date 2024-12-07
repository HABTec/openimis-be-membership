from rest_framework.permissions import BasePermission
from django.core.exceptions import ObjectDoesNotExist
from membership.utils.db_helper import SQLiteHelper  # Specific class import to be clear

class IsInsuree(BasePermission):
    """
    Custom permission to allow access only to users who are insured (insuree).
    """

    def has_permission(self, request, view):
        # Step 1: Get the current user's i_user_id
        user_id = request.user.i_user_id

        # Step 2: Use SQLiteHelper to check if user is an insuree
        db_helper = SQLiteHelper()
        insuree_id = db_helper.get_insuree_id_by_user_id(user_id)
        db_helper.close()

        # Step 3: If insuree_id exists, the user is an insuree and has permission
        return insuree_id is not None

    def has_object_permission(self, request, view, obj):
        # Object-level permissions can be implemented here if needed
        # For example, you could check if the obj belongs to the user's insuree.
        return True
