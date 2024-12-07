from core.jwt import *
from core.models import User
from core.services import user_authentication
from graphql_jwt.utils import jwt_payload
from rest_framework import exceptions


def authenticate_and_get_token(username, password, request):
    try:
        user = user_authentication(request, username, password)
        if user:
            payload = jwt_payload(user=user)
            token = jwt_encode_user_key(payload=payload, context=request)
            return {"token": token, "exp": payload['exp']}
    except exceptions.AuthenticationFailed as e:
        raise e
    except exceptions.ParseError as e:
        raise e
    return None