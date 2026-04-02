# content/filters.py
from django_filters import CharFilter, rest_framework as filters
from django_filters import FilterSet
from django.db.models import Q
import json

class BaseDynamicFilter(FilterSet):
    """
    فلتر ديناميكي عام لجميع الموديلات
    يدعم العمليات: gt, lt, gte, lte, contains, icontains, in, range, startswith, endswith, isnull
    ويدعم الربط: AND, OR, NOT
    """
    q = filters.CharFilter(method='search_all_fields', label='بحث عام')

    operator = filters.ChoiceFilter(
        choices=[('and', 'AND'), ('or', 'OR'), ('not', 'NOT')],
        method='apply_operator',
        label='الرابط المنطقي'
    )
    
    
    def search_all_fields(self, queryset, name, value):
        if not value:
            return queryset
        
        search_terms = value.split()
        q_objects = Q()
        
        text_fields = [
            field.name for field in self._meta.model._meta.get_fields()
            if field.get_internal_type() in ['CharField', 'TextField', 'SlugField']
        ]
        
        for term in search_terms:
            term_q = Q()
            for field in text_fields:
                term_q |= Q(**{f"{field}__icontains": term})
            q_objects &= term_q
        
        return queryset.filter(q_objects)
    
    def exclude_ids_filter(self, queryset, name, value):
        if not value:
            return queryset
        ids = [int(x.strip()) for x in value.split(',') if x.strip().isdigit()]
        if ids:
            return queryset.exclude(id__in=ids)
        return queryset
    
    def apply_operator(self, queryset, name, value):
        self.operator_value = value
        return queryset
    
    def filter_queryset(self, queryset):
        filters = {}
        for name, value in self.data.items():
            if name not in ['operator', 'page', 'page_size', 'ordering'] and value:
                if '__' in name:
                    filters[name] = value
                else:
                    filters[f"{name}__exact"] = value
        if self.data.get('id_ne'):
            queryset = self.filter_exclude_by_id(queryset, 'id_ne', self.data.get('id_ne'))
        if not filters:
            return queryset
        
        operator = getattr(self, 'operator_value', 'and')
        
        if operator == 'or':
            q_objects = Q()
            for field, value in filters.items():
                q_objects |= Q(**{field: value})
            return queryset.filter(q_objects)
        
        elif operator == 'not':
            q_objects = Q()
            for field, value in filters.items():
                q_objects &= Q(**{field: value})
            return queryset.exclude(q_objects)
        
        else:  
            return queryset.filter(**filters)