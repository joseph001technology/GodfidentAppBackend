import django_filters


class NoteFilter(django_filters.FilterSet):
    """Filter general notes by various criteria."""
    is_archived = django_filters.BooleanFilter()
    is_favorite = django_filters.BooleanFilter()
    is_pinned = django_filters.BooleanFilter()
    folder_id = django_filters.NumberFilter(field_name='folder_id')
    topic_id = django_filters.NumberFilter(field_name='topics__id')
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')


class RuleFilter(django_filters.FilterSet):
    """Filter Universal Rules by category and archive status."""
    category_id = django_filters.NumberFilter(field_name='category_id')
    is_archived = django_filters.BooleanFilter()