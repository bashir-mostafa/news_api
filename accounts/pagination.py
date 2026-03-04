# accounts/pagination.py
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict

class KoreanStylePagination(PageNumberPagination):
    page_size = 10 
    page_size_query_param = 'page_size'  # لتغيير العدد
    max_page_size = 100  
    page_query_param = 'page'  
    
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('pagination', OrderedDict([
                ('current_page', self.page.number),
                ('total_pages', self.page.paginator.num_pages),
                ('total_items', self.page.paginator.count),
                ('page_size', self.get_page_size(self.request)),
                ('has_next', self.page.has_next()),
                ('has_previous', self.page.has_previous()),
                ('next_page', self.page.next_page_number() if self.page.has_next() else None),
                ('previous_page', self.page.previous_page_number() if self.page.has_previous() else None),
                ('next_url', self.get_next_link()),
                ('previous_url', self.get_previous_link()),
            ])),
            ('results', data)
        ]))


class PageNumberPaginationWithRange(KoreanStylePagination):
    """
    Pagination مع عرض نطاق العناصر
    """
    def get_paginated_response(self, data):
        start_index = (self.page.number - 1) * self.get_page_size(self.request) + 1
        end_index = start_index + len(data) - 1
        
        response = super().get_paginated_response(data)
        response.data['pagination']['displaying'] = f"{start_index}-{end_index}"
        return response


class CompactPagination(PageNumberPagination):
    """
    Pagination بسيط ومضغوط
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'page': self.page.number,
            'total_pages': self.page.paginator.num_pages,
            'total': self.page.paginator.count,
            'page_size': self.get_page_size(self.request),
            'results': data
        })