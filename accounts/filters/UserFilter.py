import django_filters
from ..models import CustomUser

class UserFilter(django_filters.FilterSet):
    username = django_filters.CharFilter(lookup_expr='icontains')
    email = django_filters.CharFilter(lookup_expr='icontains')
    full_name = django_filters.CharFilter(lookup_expr='icontains')
    role = django_filters.ChoiceFilter(choices=CustomUser.Roles.choices)
    is_active = django_filters.BooleanFilter()
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role', 'is_active']