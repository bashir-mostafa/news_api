from datetime import datetime
from django.utils import timezone
from rest_framework import generics, status, filters, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from content.pagination import CompactPagination
from content.models import Categories, ContentType
from content.serializers import (
    CategoriesSerializer,
    CategoriesCreateUpdateSerializer,
    CategoriesDetailSerializer,
    CategoriesListSerializer
)
from news_api.permission import IsAdminOrReadOnly, IsAdmin

# ============ LIST & CREATE ============
class CategoryListCreateView(generics.ListCreateAPIView):
    """
    عرض قائمة التصنيفات وإنشاء تصنيف جديد
    GET: /api/categories/
    POST: /api/categories/
    """
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    pagination_class = CompactPagination
    search_fields = ['name_ar', 'name_ku', 'name_en', 'description']
    ordering_fields = ['created_at', 'name_ar', 'name_en', 'name_ku', 'slug', 'content_type__priority']
    ordering = ['content_type__priority', 'name_ar']  # ترتيب حسب الأولوية ثم الاسم
    
    def get_queryset(self):
        queryset = Categories.objects.filter(deleted_at__isnull=True).select_related('content_type')
        
        # ===== فلترة حسب نوع المحتوى =====
        content_type_id = self.request.query_params.get('content_type')
        if content_type_id:
            try:
                queryset = queryset.filter(content_type_id=int(content_type_id))
            except ValueError:
                pass
        
        # ===== فلترة حسب التاريخ =====
        created_at_gte = self.request.query_params.get('createdAt_gte')
        created_at_lte = self.request.query_params.get('createdAt_lte')
        
        if created_at_gte:
            try:
                dt = datetime.strptime(created_at_gte, '%Y-%m-%d')
                aware_dt = timezone.make_aware(dt)
                queryset = queryset.filter(created_at__gte=aware_dt)
            except (ValueError, TypeError):
                pass
        
        if created_at_lte:
            try:
                dt = datetime.strptime(created_at_lte, '%Y-%m-%d')
                dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
                aware_dt = timezone.make_aware(dt)
                queryset = queryset.filter(created_at__lte=aware_dt)
            except (ValueError, TypeError):
                pass
        
        # ===== فلترة حسب الاسم =====
        name_ar = self.request.query_params.get('name_ar')
        name_en = self.request.query_params.get('name_en')
        name_ku = self.request.query_params.get('name_ku')
        
        if name_ar:
            queryset = queryset.filter(name_ar__icontains=name_ar)
        
        if name_en:
            queryset = queryset.filter(name_en__icontains=name_en)
        
        if name_ku:
            queryset = queryset.filter(name_ku__icontains=name_ku)
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return CategoriesListSerializer
        return CategoriesCreateUpdateSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    
    def perform_create(self, serializer):
        serializer.save()
    
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            category = Categories.objects.get(id=serializer.instance.id)
            detail_serializer = CategoriesDetailSerializer(category, context={'request': request})
            
            return Response({
                "message": "category created successfully",
                "data": detail_serializer.data
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
                serializer = self.get_serializer(page, many=True, context={'request': request})
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(queryset, many=True, context={'request': request})
            return Response({
                "message": "get all categories successfully",
                "count": queryset.count(),
                "data": serializer.data
            })
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ RETRIEVE, UPDATE, DELETE ============
class CategoryRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """
    عرض وتحديث وحذف تصنيف معين
    GET: /api/categories/{id}/
    PUT: /api/categories/{id}/
    PATCH: /api/categories/{id}/
    DELETE: /api/categories/{id}/
    """
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'id'
    
    def get_queryset(self):
        return Categories.objects.filter(deleted_at__isnull=True).select_related('content_type')
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return CategoriesCreateUpdateSerializer
        return CategoriesDetailSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, context={'request': request})
            
            return Response({
                "message": "get category details successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
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
            
            updated_instance = self.get_object()
            detail_serializer = CategoriesDetailSerializer(updated_instance, context={'request': request})
            
            return Response({
                "message": "category updated successfully",
                "data": detail_serializer.data
            }, status=status.HTTP_200_OK)
            
        except serializers.ValidationError as e:
            return Response({
                "message": e.detail
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            
            # التحقق من وجود مقالات مرتبطة قبل الحذف
            if instance.posts.filter(deleted_at__isnull=True).exists():
                return Response({
                    "message": "لا يمكن حذف التصنيف لأنه يحتوي على مقالات"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            instance.deleted_at = timezone.now()
            instance.save()
            
            return Response({
                "message": "category deleted successfully"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ HARD DELETE ============
class CategoryHardDeleteView(generics.DestroyAPIView):
    """
    حذف نهائي لتصنيف (للمشرفين فقط)
    DELETE: /api/categories/hard-delete/{id}/
    """
    permission_classes = [IsAdmin]
    lookup_field = 'id'
    
    def get_queryset(self):
        return Categories.objects.all()
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            category_name = instance.name_en
            instance.delete()
            
            return Response({
                "message": f"category '{category_name}' deleted permanently successfully"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class CategoryBulkHardDeleteView(APIView):
    """
    حذف نهائي لعدة تصنيفات (للمشرفين فقط)
    DELETE: /api/categories/bulk-hard-delete/
    """
    permission_classes = [IsAdmin]

    def delete(self, request):
        category_ids = request.data.get('ids', [])
        
        if not category_ids:
            return Response({
                "message": "please provide ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(category_ids, list):
            return Response({
                "message": "category_ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get categories to return their names in response
        categories = Categories.objects.filter(id__in=category_ids)
        found_ids = list(categories.values_list('id', flat=True))
        
        if not found_ids:
            return Response({
                "message": "no categories found with the provided ids"
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Store category names for response message
        category_names = list(categories.values_list('name_en', flat=True))
        deleted_count = len(found_ids)
        
        # Permanent delete
        categories.delete()
        
        return Response({
            "message": f"{deleted_count} out of {len(category_ids)} categories deleted permanently successfully",
            "deleted_ids": found_ids,
            "deleted_names": category_names
        }, status=status.HTTP_200_OK)


# ============ RESTORE DELETED ============
class CategoryRestoreView(APIView):
    """
    استعادة تصنيف محذوف
    POST: /api/categories/restore/{id}/
    """
    permission_classes = [IsAdmin]
    
    def post(self, request, id):
        try:
            category = Categories.objects.get(id=id, deleted_at__isnull=False)
            category.deleted_at = None
            category.save()
            
            serializer = CategoriesDetailSerializer(category, context={'request': request})
            return Response({
                "message": "category restored successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Categories.DoesNotExist:
            return Response({
                "message": "category not found or not deleted"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ BULK DELETE ============
class CategoryBulkDeleteView(APIView):
    """
    حذف مؤقت لعدة تصنيفات
    DELETE: /api/categories/bulk-delete/
    """
    permission_classes = [IsAdmin]

    def delete(self, request):
        category_ids = request.data.get('ids', [])
        
        if not category_ids:
            return Response({
                "message": "please provide category_ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(category_ids, list):
            return Response({
                "message": "category_ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # التحقق من وجود مقالات قبل الحذف
        categories_to_delete = Categories.objects.filter(
            id__in=category_ids, 
            deleted_at__isnull=True
        )
        
        # التحقق من أن التصنيفات ليس بها مقالات
        for category in categories_to_delete:
            if category.posts.filter(deleted_at__isnull=True).exists():
                return Response({
                    "message": f"لا يمكن حذف التصنيف '{category.name_ar}' لأنه يحتوي على مقالات"
                }, status=status.HTTP_400_BAD_REQUEST)
        
        deleted_count = categories_to_delete.update(deleted_at=timezone.now())
        
        if deleted_count == 0:
            return Response({
                "message": "no categories were deleted. they may already be deleted or not exist."
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "message": f"{deleted_count} out of {len(category_ids)} categories deleted successfully"
        }, status=status.HTTP_200_OK)


# ============ BULK RESTORE ============
class CategoryBulkRestoreView(APIView):
    """
    استعادة عدة تصنيفات محذوفة
    POST: /api/categories/bulk-restore/
    """
    permission_classes = [IsAdmin]

    def post(self, request):
        category_ids = request.data.get('ids', [])
        
        if not category_ids:
            return Response({
                "message": "please provide category_ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(category_ids, list):
            return Response({
                "message": "category_ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        restored_count = Categories.objects.filter(
            id__in=category_ids, 
            deleted_at__isnull=False
        ).update(deleted_at=None)
        
        if restored_count == 0:
            return Response({
                "message": "no categories were restored. they may not be deleted or not exist."
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "message": f"{restored_count} out of {len(category_ids)} categories restored successfully"
        }, status=status.HTTP_200_OK)


# ============ CATEGORIES BY CONTENT TYPE ============
class CategoriesByContentView(generics.ListAPIView):
 
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = CategoriesListSerializer
    pagination_class = CompactPagination
    
    def get_queryset(self):
        content_type_id = self.kwargs.get('content_type_id')
        return Categories.objects.filter(
            content_type_id=content_type_id,
            deleted_at__isnull=True
        ).select_related('content_type')
    
    def list(self, request, *args, **kwargs):
        try:
            content_type_id = self.kwargs.get('content_type_id')
            
            if not ContentType.objects.filter(id=content_type_id, deleted_at__isnull=True).exists():
                return Response({
                    "message": "Content type not found"
                }, status=status.HTTP_404_NOT_FOUND)
            
            return super().list(request, *args, **kwargs)
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ GET DELETED CATEGORIES ============
class CategoryDeletedListView(generics.ListAPIView):
    """
    عرض التصنيفات المحذوفة
    GET: /api/categories/deleted/
    """
    permission_classes = [IsAdmin]
    serializer_class = CategoriesListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name_ar', 'name_ku', 'name_en']
    pagination_class = CompactPagination
    
    def get_queryset(self):
        return Categories.objects.filter(deleted_at__isnull=False).select_related('content_type')