# content/views/publications_views.py
from rest_framework import generics, status, filters, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from content.pagination import CompactPagination
from content.models import Publications
from content.serializers import (
    PublicationsSerializer,
    PublicationsCreateUpdateSerializer,
    PublicationsDetailSerializer,
    PublicationsListSerializer,
    PublicationsDeletedListSerializer
)

# ============ LIST & CREATE ============
class PublicationListCreateView(generics.ListCreateAPIView):
    """
    عرض قائمة النشرات وإنشاء نشرة جديدة
    GET: /api/publications/
    POST: /api/publications/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['id', 'post', 'publication_type', 'publish_year']
    pagination_class = CompactPagination
    search_fields = ['publication_type', 'issue_number', 'volume', 'isbn']
    ordering_fields = ['created_at', 'publish_year', 'page_count']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Publications.objects.filter(deleted_at__isnull=True)
        
        # تصفية حسب المقال
        post_id = self.request.query_params.get('post')
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        
        # تصفية حسب نوع النشر
        publication_type = self.request.query_params.get('publication_type')
        if publication_type:
            queryset = queryset.filter(publication_type=publication_type)
        
        # تصفية حسب سنة النشر
        publish_year = self.request.query_params.get('publish_year')
        if publish_year:
            queryset = queryset.filter(publish_year=publish_year)
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PublicationsListSerializer
        return PublicationsCreateUpdateSerializer
    
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
            
            publication = Publications.objects.get(id=serializer.instance.id)
            detail_serializer = PublicationsDetailSerializer(publication, context={'request': request})
            
            return Response({
                "message": "publication created successfully",
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
                "message": "get all publications successfully",
                "count": queryset.count(),
                "data": serializer.data
            })
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ RETRIEVE, UPDATE, DELETE ============
class PublicationRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """
    عرض وتحديث وحذف نشرة محددة
    GET: /api/publications/{id}/
    PUT: /api/publications/{id}/
    PATCH: /api/publications/{id}/
    DELETE: /api/publications/{id}/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'id'
    
    def get_queryset(self):
        return Publications.objects.filter(deleted_at__isnull=True)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PublicationsCreateUpdateSerializer
        return PublicationsDetailSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, context={'request': request})
            
            return Response({
                "message": "get publication details successfully",
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
            detail_serializer = PublicationsDetailSerializer(updated_instance, context={'request': request})
            
            return Response({
                "message": "publication updated successfully",
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
                "message": "publication deleted successfully"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ HARD DELETE ============
class PublicationHardDeleteView(generics.DestroyAPIView):
    """
    حذف نهائي لنشرة (للمشرفين فقط)
    DELETE: /api/publications/hard-delete/{id}/
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'id'
    queryset = Publications.objects.all()
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            publication_id = instance.id
            instance.delete()
            
            return Response({
                "message": f"publication '{publication_id}' deleted permanently successfully"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class PublicationBulkHardDeleteView(APIView):
    """
    حذف نهائي لمجموعة نشرات (للمشرفين فقط)
    DELETE: /api/publications/bulk-hard-delete/
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request):
        publication_ids = request.data.get('ids', [])
        
        if not publication_ids:
            return Response({
                "message": "please provide ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(publication_ids, list):
            return Response({
                "message": "ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        publications = Publications.objects.filter(id__in=publication_ids)
        found_ids = list(publications.values_list('id', flat=True))
        
        if not found_ids:
            return Response({
                "message": "no publications found with the provided ids"
            }, status=status.HTTP_404_NOT_FOUND)
        
        deleted_count = len(found_ids)
        publications.delete()
        
        return Response({
            "message": f"{deleted_count} out of {len(publication_ids)} publications deleted permanently successfully",
            "deleted_ids": found_ids
        }, status=status.HTTP_200_OK)


# ============ RESTORE DELETED ============
class PublicationRestoreView(APIView):
    """
    استعادة نشرة محذوفة
    POST: /api/publications/restore/{id}/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, id):
        try:
            publication = Publications.objects.get(id=id, deleted_at__isnull=False)
            publication.deleted_at = None
            publication.save()
            
            serializer = PublicationsDetailSerializer(publication, context={'request': request})
            return Response({
                "message": "publication restored successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Publications.DoesNotExist:
            return Response({
                "message": "publication not found or not deleted"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ BULK DELETE ============
class PublicationBulkDeleteView(APIView):
    """
    حذف ناعم لمجموعة نشرات
    DELETE: /api/publications/bulk-delete/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def delete(self, request):
        publication_ids = request.data.get('ids', [])
        
        if not publication_ids:
            return Response({
                "message": "please provide ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(publication_ids, list):
            return Response({
                "message": "ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        deleted_count = Publications.objects.filter(
            id__in=publication_ids, 
            deleted_at__isnull=True
        ).update(deleted_at=timezone.now())
        
        if deleted_count == 0:
            return Response({
                "message": "no publications were deleted. they may already be deleted or not exist."
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "message": f"{deleted_count} out of {len(publication_ids)} publications deleted successfully"
        }, status=status.HTTP_200_OK)


# ============ BULK RESTORE ============
class PublicationBulkRestoreView(APIView):
    """
    استعادة مجموعة نشرات محذوفة
    POST: /api/publications/bulk-restore/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request):
        publication_ids = request.data.get('ids', [])
        
        if not publication_ids:
            return Response({
                "message": "please provide ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(publication_ids, list):
            return Response({
                "message": "ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        restored_count = Publications.objects.filter(
            id__in=publication_ids, 
            deleted_at__isnull=False
        ).update(deleted_at=None)
        
        if restored_count == 0:
            return Response({
                "message": "no publications were restored. they may not be deleted or not exist."
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "message": f"{restored_count} out of {len(publication_ids)} publications restored successfully"
        }, status=status.HTTP_200_OK)


# ============ GET DELETED PUBLICATIONS ============
class PublicationDeletedListView(generics.ListAPIView):
    """
    عرض قائمة النشرات المحذوفة
    GET: /api/publications/deleted/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = PublicationsDeletedListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['post', 'publication_type', 'publish_year']
    search_fields = ['publication_type', 'issue_number', 'volume', 'isbn']
    ordering_fields = ['deleted_at', 'created_at', 'publish_year']
    ordering = ['-deleted_at']
    pagination_class = CompactPagination
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    
    def get_queryset(self):
        return Publications.objects.filter(deleted_at__isnull=False)


# ============ GET PUBLICATIONS BY POST ============
class PublicationsByPostView(generics.ListAPIView):
    """
    عرض نشرات مقال محدد
    GET: /api/publications/by-post/{post_id}/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = PublicationsListSerializer
    pagination_class = CompactPagination
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    
    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        return Publications.objects.filter(
            post_id=post_id,
            deleted_at__isnull=True
        )