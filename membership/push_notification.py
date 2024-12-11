# from membership.utils.db_helper import SQLiteHelper
# from rest_framework import status
# from rest_framework.response import Response
# from rest_framework.views import APIView

# class SaveFirebaseTokenView(APIView):
#     """
#     API view to save or update Firebase token for a user.
#     """
#     def post(self, request, *args, **kwargs):
#         user_id = request.data.get('user_id')
#         fcm_token = request.data.get('fcm_token')

#         # Validate inputs
#         if not user_id or not fcm_token:
#             return Response(
#                 {"error": "user_id and fcm_token are required."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         # Initialize SQLiteHelper
#         db_helper = SQLiteHelper()

#         # Save or update the Firebase token in the database
#         db_helper.insert_fcm_token(user_id, fcm_token)
#         db_helper.close()

#         return Response(
#             {"message": "Firebase token saved successfully."},
#             status=status.HTTP_201_CREATED
#         )