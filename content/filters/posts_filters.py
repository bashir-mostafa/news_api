# content/filters/posts.py
from django_filters import rest_framework as filters
from django_filters import CharFilter
from django.db import models
from content.models import Posts
from content.filters.filters import BaseDynamicFilter

class PostsFilter(BaseDynamicFilter):
    
    id_ne = CharFilter(method='filter_exclude_by_id', label='استبعاد ID')
    id_in = CharFilter(method='include_ids_filter', label='تضمين IDs')

    def filter_exclude_by_id(self, queryset, name, value):
        """استبعاد ID محدد"""
        if value:
            return queryset.exclude(id=value)
        return queryset
    
    class Meta:
        model = Posts
       
        fields = '__all__'
        exclude = ['featured_image']  
        
      
        
        filter_overrides = {
            models.ImageField: {
                'filter_class': CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
            models.DateTimeField: {
                'filter_class': filters.DateTimeFilter,
                'extra': lambda f: {
                    'lookup_expr': 'exact',
                },
            },
            models.BooleanField: {
                'filter_class': filters.BooleanFilter,
                'extra': lambda f: {
                    'widget': None,
                },
            },
        }