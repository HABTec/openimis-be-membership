from rest_framework import status
from rest_framework.response import Response

def success_response(data=None, message="Success", status_code=status.HTTP_200_OK):
    response = {
        "error": False,
        "message": message,
        "data": data
    }
    return Response(response, status_code=status_code)

def error_response(message="An error occurred", errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    response = {
        "error": True,
        "message": message,
        "errors": errors
    }
    return Response(response, status=status_code)
