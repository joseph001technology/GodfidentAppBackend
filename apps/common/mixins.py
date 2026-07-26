"""Shared utility mixins for viewsets."""


class OwnerModelMixin:
    """Mixin that automatically sets the owner (user) on object creation
    and filters queryset by the current user."""

    owner_field = 'user'

    def get_queryset(self):
        return self.queryset.filter(**{self.owner_field: self.request.user})

    def perform_create(self, serializer):
        serializer.save(**{self.owner_field: self.request.user})


class SerializerContextMixin:
    """Ensures request is in serializer context."""

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class SuccessResponseMixin:
    """Wraps list/create responses in {'success': True, 'data': ...} format."""

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if isinstance(response.data, dict) and 'results' in response.data:
            response.data['success'] = True
        return response

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code in (200, 201) and 'success' not in response.data:
            response.data = {'success': True, 'data': response.data}
        return response

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        if response.status_code == 200 and 'success' not in response.data:
            response.data = {'success': True, 'data': response.data}
        return response

