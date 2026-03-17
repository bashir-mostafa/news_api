from rest_framework import generics, status, filters, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from content.pagination import CompactPagination
from content.models import Categories
from content.serializers import (
    CategoriesSerializer,
    CategoriesCreateUpdateSerializer,
    CategoriesDetailSerializer,
    CategoriesListSerializer
)

# ============ LIST & CREATE ============
class CategoryListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['id']
    pagination_class = CompactPagination
    search_fields = ['name_ar', 'name_ku', 'name_en', 'description']
    ordering_fields = ['created_at', 'name_ar', 'name_en', 'name_ku', 'slug']
    ordering = ['name_ar']
    
    def get_queryset(self):
        return Categories.objects.filter(deleted_at__isnull=True)
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return CategoriesListSerializer
        return CategoriesCreateUpdateSerializer
    
    def perform_create(self, serializer):
        serializer.save()
    
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            category = Categories.objects.get(id=serializer.instance.id)
            detail_serializer = CategoriesDetailSerializer(category)
            
            return Response({
                "message": "category created successfully",
                "data": detail_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except serializers.ValidationError as e:
            return Response({
                "message": e.detail
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
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'id'
    
    def get_queryset(self):
        return Categories.objects.filter(deleted_at__isnull=True)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return CategoriesCreateUpdateSerializer
        return CategoriesDetailSerializer
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            
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
            detail_serializer = CategoriesDetailSerializer(updated_instance)
            
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
    permission_classes = [IsAuthenticated, IsAdminUser]
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
    Bulk hard delete categories (permanent deletion - admin only)
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

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
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def post(self, request, id):
        try:
            category = Categories.objects.get(id=id, deleted_at__isnull=False)
            category.deleted_at = None
            category.save()
            
            serializer = CategoriesDetailSerializer(category)
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
    permission_classes = [IsAuthenticatedOrReadOnly]

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
        
        deleted_count = Categories.objects.filter(
            id__in=category_ids, 
            deleted_at__isnull=True
        ).update(deleted_at=timezone.now())
        
        if deleted_count == 0:
            return Response({
                "message": "no categories were deleted. they may already be deleted or not exist."
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "message": f"{deleted_count} out of {len(category_ids)} categories deleted successfully"
        }, status=status.HTTP_200_OK)


# ============ BULK RESTORE ============
class CategoryBulkRestoreView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

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