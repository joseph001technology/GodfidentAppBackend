from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    """Standardized error responses across all endpoints."""
    response = exception_handler(exc, context)

    if response is not None:
        error_code = 'ERROR'
        message = str(exc)

        if response.status_code == 404:
            error_code = 'NOT_FOUND'
        elif response.status_code == 401:
            error_code = 'UNAUTHORIZED'
        elif response.status_code == 403:
            error_code = 'FORBIDDEN'
        elif response.status_code == 400:
            error_code = 'VALIDATION_ERROR'
        elif response.status_code == 429:
            error_code = 'RATE_LIMITED'
        elif response.status_code >= 500:
            error_code = 'SERVER_ERROR'

        detail = response.data
        if isinstance(detail, dict) and 'detail' in detail:
            message = str(detail['detail'])

        response.data = {
            'success': False,
            'error_code': error_code,
            'message': message,
            'errors': response.data if isinstance(response.data, dict) else None,
        }

    return response
