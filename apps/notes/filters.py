import django_filters
from rest_framework import filters


class NoteFilter(django_filters.FilterSet):
    """Filter notes by various criteria."""
    from django_filters import rest_framework as drf_filters

    is_archived = drf_filters.BooleanFilter()
    is_favorite = drf_filters.BooleanFilter()
    is_pinned = drf_filters.BooleanFilter()
    folder_id = drf_filters.NumberFilter()
    topic_id = drf_filters.NumberFilter(field_name='topics__id')
    created_after = drf_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = drf_filters.DateFilter(field_name='created_at', lookup_expr='lte')
