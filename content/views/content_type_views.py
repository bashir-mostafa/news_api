# content/views/content_type_views.py

from rest_framework import generics, status, filters, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from content.models import ContentType, Categories  
from content.serializers import (
    ContentTypeSerializer, 
    ContentTypeCreateUpdateSerializer,
    CategoriesSerializer,
    CategoriesCreateUpdateSerializer,
    CategoriesDetailSerializer
)
from news_api.permission import IsAdmin, IsAdminOrReadOnly, AllowAny
from content.pagination import CompactPagination


# ============ CONTENT TYPE VIEWS ============

class ContentTypeListCreateView(generics.ListCreateAPIView):  # تم التعديل: أزلت Post من الاسم
    """
    عرض قائمة أنواع المحتوى وإنشاء نوع جديد
    GET: /api/content-types/
    POST: /api/content-types/
    """
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['id', 'priority']
    search_fields = ['name_ar', 'name_en', 'name_ku']
    ordering_fields = ['priority', 'name_ar', 'created_at']
    ordering = ['priority', 'name_ar']
    pagination_class = CompactPagination
    
    def get_queryset(self):
        return ContentType.objects.filter(deleted_at__isnull=True)  # تم التعديل
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ContentTypeSerializer
        return ContentTypeCreateUpdateSerializer
    
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            return Response({
                "message": "Content type created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except serializers.ValidationError as e:
            return Response({
                "message": e.detail
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                "message": "Content types retrieved successfully",
                "count": queryset.count(),
                "data": serializer.data
            })
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ContentTypeRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):  # تم التعديل
    """
    عرض وتحديث وحذف نوع محتوى معين
    GET: /api/content-types/{id}/
    PUT/PATCH: /api/content-types/{id}/
    DELETE: /api/content-types/{id}/
    """
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'id'
    
    def get_queryset(self):
        return ContentType.objects.filter(deleted_at__isnull=True)  # تم التعديل
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ContentTypeCreateUpdateSerializer
        return ContentTypeSerializer
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            
            categories = Categories.objects.filter(
                content_type=instance,  # تم التعديل
                deleted_at__isnull=True
            )
            categories_serializer = CategoriesSerializer(categories, many=True)
            
            return Response({
                "message": "Content type retrieved successfully",
                "data": serializer.data,
                "categories": categories_serializer.data
            })
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_404_NOT_FOUND)
    
    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            
            return Response({
                "message": "Content type updated successfully",
                "data": serializer.data
            })
        except serializers.ValidationError as e:
            return Response({
                "message": e.detail
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            
            if Categories.objects.filter(content_type=instance, deleted_at__isnull=True).exists():  # تم التعديل
                return Response({
                    "message": "لا يمكن حذف نوع المحتوى لأنه يحتوي على تصنيفات"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            instance.deleted_at = timezone.now()
            instance.save()
            
            return Response({
                "message": "Content type deleted successfully"
            })
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ CATEGORIES VIEWS ============

class CategoriesListCreateView(generics.ListCreateAPIView):
    """
    عرض قائمة التصنيفات وإنشاء تصنيف جديد
    GET: /api/categories/
    POST: /api/categories/
    """
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['id', 'content_type']  # تم التعديل
    search_fields = ['name_ar', 'name_en', 'name_ku']
    ordering_fields = ['name_ar', 'created_at', 'content_type__priority']  # تم التعديل
    ordering = ['name_ar']
    pagination_class = CompactPagination
    
    def get_queryset(self):
        queryset = Categories.objects.filter(deleted_at__isnull=True)
        
        content_type_id = self.request.query_params.get('content_type')  # تم التعديل
        if content_type_id:
            queryset = queryset.filter(content_type_id=content_type_id)  # تم التعديل
        
        return queryset.select_related('content_type')  # تم التعديل
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return CategoriesSerializer
        return CategoriesCreateUpdateSerializer
    
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            return Response({
                "message": "Category created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except serializers.ValidationError as e:
            return Response({
                "message": e.detail
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class CategoriesRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """
    عرض وتحديث وحذف تصنيف معين
    GET: /api/categories/{id}/
    PUT/PATCH: /api/categories/{id}/
    DELETE: /api/categories/{id}/
    """
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'id'
    
    def get_queryset(self):
        return Categories.objects.filter(deleted_at__isnull=True).select_related('content_type')  # تم التعديل
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return CategoriesCreateUpdateSerializer
        return CategoriesDetailSerializer
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            
            return Response({
                "message": "Category retrieved successfully",
                "data": serializer.data
            })
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_404_NOT_FOUND)
    
    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            
            return Response({
                "message": "Category updated successfully",
                "data": serializer.data
            })
        except serializers.ValidationError as e:
            return Response({
                "message": e.detail
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            
            if instance.posts.filter(deleted_at__isnull=True).exists():
                return Response({
                    "message": "لا يمكن حذف التصنيف لأنه يحتوي على مقالات"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            instance.deleted_at = timezone.now()
            instance.save()
            
            return Response({
                "message": "Category deleted successfully"
            })
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ CATEGORIES BY CONTENT TYPE ============

class CategoriesByContentTypeView(generics.ListAPIView): 
    """
    عرض التصنيفات حسب نوع المحتوى
    GET: /api/content-types/{content_type_id}/categories/
    """
    permission_classes = [AllowAny]
    serializer_class = CategoriesSerializer
    pagination_class = CompactPagination
    
    def get_queryset(self):
        content_type_id = self.kwargs.get('content_type_id')  
        return Categories.objects.filter(
            content_type_id=content_type_id, 
            deleted_at__isnull=True
        ).select_related('content_type')  