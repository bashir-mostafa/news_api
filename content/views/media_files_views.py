# content/views/media_files_views.py
from rest_framework import generics, status, filters, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from content.pagination import CompactPagination
from content.models import MediaFiles
from content.serializers import (
    MediaFilesSerializer,
    MediaFilesCreateUpdateSerializer,
    MediaFilesDetailSerializer,
    MediaFilesListSerializer,
    MediaFilesDeletedListSerializer
)

# ============ LIST & CREATE ============
class MediaFileListCreateView(generics.ListCreateAPIView):
    """
    عرض قائمة ملفات الوسائط وإنشاء ملف جديد
    GET: /api/media-files/
    POST: /api/media-files/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['id', 'post', 'file_type']
    pagination_class = CompactPagination
    search_fields = ['alt_text', 'caption']
    ordering_fields = ['created_at', 'file_size_kb']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = MediaFiles.objects.filter(deleted_at__isnull=True)
        
        # تصفية حسب المقال
        post_id = self.request.query_params.get('post')
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        
        # تصفية حسب نوع الملف
        file_type = self.request.query_params.get('file_type')
        if file_type:
            queryset = queryset.filter(file_type=file_type)
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return MediaFilesListSerializer
        return MediaFilesCreateUpdateSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            media_file = MediaFiles.objects.get(id=serializer.instance.id)
            detail_serializer = MediaFilesDetailSerializer(media_file, context={'request': request})
            
            return Response({
                "message": "media file created successfully",
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
                "message": "get all media files successfully",
                "count": queryset.count(),
                "data": serializer.data
            })
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ RETRIEVE, UPDATE, DELETE ============
class MediaFileRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """
    عرض وتحديث وحذف ملف وسائط محدد
    GET: /api/media-files/{id}/
    PUT: /api/media-files/{id}/
    PATCH: /api/media-files/{id}/
    DELETE: /api/media-files/{id}/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'id'
    
    def get_queryset(self):
        return MediaFiles.objects.filter(deleted_at__isnull=True)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return MediaFilesCreateUpdateSerializer
        return MediaFilesDetailSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, context={'request': request})
            
            return Response({
                "message": "get media file details successfully",
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
            detail_serializer = MediaFilesDetailSerializer(updated_instance, context={'request': request})
            
            return Response({
                "message": "media file updated successfully",
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
                "message": "media file deleted successfully"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ HARD DELETE ============
class MediaFileHardDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'id'
    queryset = MediaFiles.objects.all()
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            media_id = instance.id
            instance.delete()
            
            return Response({
                "message": f"media file '{media_id}' deleted permanently successfully"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class MediaFileBulkHardDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request):
        media_ids = request.data.get('ids', [])
        
        if not media_ids:
            return Response({
                "message": "please provide ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(media_ids, list):
            return Response({
                "message": "ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        media_files = MediaFiles.objects.filter(id__in=media_ids)
        found_ids = list(media_files.values_list('id', flat=True))
        
        if not found_ids:
            return Response({
                "message": "no media files found with the provided ids"
            }, status=status.HTTP_404_NOT_FOUND)
        
        deleted_count = len(found_ids)
        media_files.delete()
        
        return Response({
            "message": f"{deleted_count} out of {len(media_ids)} media files deleted permanently successfully",
            "deleted_ids": found_ids
        }, status=status.HTTP_200_OK)


# ============ RESTORE DELETED ============
class MediaFileRestoreView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, id):
        try:
            media_file = MediaFiles.objects.get(id=id, deleted_at__isnull=False)
            media_file.deleted_at = None
            media_file.save()
            
            serializer = MediaFilesDetailSerializer(media_file, context={'request': request})
            return Response({
                "message": "media file restored successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except MediaFiles.DoesNotExist:
            return Response({
                "message": "media file not found or not deleted"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ BULK DELETE ============
class MediaFileBulkDeleteView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def delete(self, request):
        media_ids = request.data.get('ids', [])
        
        if not media_ids:
            return Response({
                "message": "please provide ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(media_ids, list):
            return Response({
                "message": "ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        deleted_count = MediaFiles.objects.filter(
            id__in=media_ids, 
            deleted_at__isnull=True
        ).update(deleted_at=timezone.now())
        
        if deleted_count == 0:
            return Response({
                "message": "no media files were deleted. they may already be deleted or not exist."
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "message": f"{deleted_count} out of {len(media_ids)} media files deleted successfully"
        }, status=status.HTTP_200_OK)


# ============ BULK RESTORE ============
class MediaFileBulkRestoreView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request):
        media_ids = request.data.get('ids', [])
        
        if not media_ids:
            return Response({
                "message": "please provide ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(media_ids, list):
            return Response({
                "message": "ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        restored_count = MediaFiles.objects.filter(
            id__in=media_ids, 
            deleted_at__isnull=False
        ).update(deleted_at=None)
        
        if restored_count == 0:
            return Response({
                "message": "no media files were restored. they may not be deleted or not exist."
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "message": f"{restored_count} out of {len(media_ids)} media files restored successfully"
        }, status=status.HTTP_200_OK)


# ============ GET DELETED MEDIA FILES ============
class MediaFileDeletedListView(generics.ListAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = MediaFilesDeletedListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['post', 'file_type']
    search_fields = ['alt_text', 'caption']
    ordering_fields = ['deleted_at', 'created_at']
    ordering = ['-deleted_at']
    pagination_class = CompactPagination
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    
    def get_queryset(self):
        return MediaFiles.objects.filter(deleted_at__isnull=False)


# ============ GET MEDIA FILES BY POST ============
class MediaFilesByPostView(generics.ListAPIView):
    """
    عرض ملفات وسائط مقال محدد
    GET: /api/media-files/by-post/{post_id}/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = MediaFilesListSerializer
    pagination_class = CompactPagination
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    
    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        return MediaFiles.objects.filter(
            post_id=post_id,
            deleted_at__isnull=True
        )