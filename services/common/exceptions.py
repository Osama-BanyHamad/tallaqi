from rest_framework import exceptions, status
from rest_framework.views import exception_handler as drf_handler


class CapabilityDisabled(exceptions.APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "This module is not enabled for the tenant."
    default_code = "capability_disabled"


class PermissionDenied(exceptions.APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You do not have permission to perform this action."
    default_code = "permission_denied"


class DomainError(exceptions.APIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Domain rule violated."
    default_code = "domain_error"


def exception_handler(exc, ctx):
    response = drf_handler(exc, ctx)
    if response is not None and isinstance(response.data, dict) and "code" not in response.data:
        code = getattr(exc, "default_code", "error")
        detail = response.data.get("detail", response.data)
        response.data = {"code": code, "detail": detail}
    return response
