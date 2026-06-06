from rest_framework.views import exception_handler
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """Standardized error responses across all endpoints."""
    response = exception_handler(exc, context)

    if response is not None:
        error_code = 'ERROR'
        message = str(exc)

        # Map common exceptions to error codes
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

        # Flatten DRF validation error detail
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


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'success': True,
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        })
