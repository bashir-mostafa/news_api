# content/views/comments_views.py
from rest_framework import generics, status, filters, serializers
from rest_framework.response import Response
from news_api.permission import IsAdmin, IsAdminOrReadOnly, AllowAny
from rest_framework.views import APIView
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from content.pagination import CompactPagination
from content.models import Comments
from content.serializers import (
    CommentsSerializer,
    CommentsCreateUpdateSerializer,
    CommentsDetailSerializer,
    CommentsListSerializer,
    CommentsDeletedListSerializer
)

# ============ LIST & CREATE ============
class CommentListCreateView(generics.ListCreateAPIView):
    """
    عرض قائمة التعليقات وإنشاء تعليق جديد
    GET: /api/comments/
    POST: /api/comments/
    """
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['id', 'post', 'is_approved', 'name', 'email']
    pagination_class = CompactPagination
    search_fields = ['name', 'email', 'comment']
    ordering_fields = ['created_at', 'name', 'is_approved']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Comments.objects.filter(deleted_at__isnull=True)
        
        post_id = self.request.query_params.get('post')
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        
        if not self.request.user.is_authenticated or not self.request.user.is_staff:
            queryset = queryset.filter(is_approved=True)
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return CommentsListSerializer
        return CommentsCreateUpdateSerializer
    
    def perform_create(self, serializer):
        serializer.save()
    
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            comment = Comments.objects.get(id=serializer.instance.id)
            detail_serializer = CommentsDetailSerializer(comment)
            
            return Response({
                "message": "comment created successfully",
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
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                "message": "get all comments successfully",
                "count": queryset.count(),
                "data": serializer.data
            })
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ RETRIEVE, UPDATE, DELETE ============
class CommentRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'id'
    
    def get_queryset(self):
        queryset = Comments.objects.filter(deleted_at__isnull=True)
        
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_approved=True)
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return CommentsCreateUpdateSerializer
        return CommentsDetailSerializer
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            
            return Response({
                "message": "get comment details successfully",
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
            detail_serializer = CommentsDetailSerializer(updated_instance)
            
            return Response({
                "message": "comment updated successfully",
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
                "message": "comment deleted successfully"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ HARD DELETE ============
class CommentHardDeleteView(generics.DestroyAPIView):

    permission_classes = [IsAdmin]
    lookup_field = 'id'
    queryset = Comments.objects.all()
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            comment_id = instance.id
            instance.delete()
            
            return Response({
                "message": f"comment '{comment_id}' deleted permanently successfully"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class CommentBulkHardDeleteView(APIView):
    """
    حذف نهائي لمجموعة تعليقات (للمشرفين فقط)
    DELETE: /api/comments/bulk-hard-delete/
    """
    permission_classes = [IsAdminOrReadOnly]

    def delete(self, request):
        comment_ids = request.data.get('ids', [])
        
        if not comment_ids:
            return Response({
                "message": "please provide ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(comment_ids, list):
            return Response({
                "message": "ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        comments = Comments.objects.filter(id__in=comment_ids)
        found_ids = list(comments.values_list('id', flat=True))
        
        if not found_ids:
            return Response({
                "message": "no comments found with the provided ids"
            }, status=status.HTTP_404_NOT_FOUND)
        
        deleted_count = len(found_ids)
        comments.delete()
        
        return Response({
            "message": f"{deleted_count} out of {len(comment_ids)} comments deleted permanently successfully",
            "deleted_ids": found_ids
        }, status=status.HTTP_200_OK)


# ============ RESTORE DELETED ============
class CommentRestoreView(APIView):
    """
    استعادة تعليق محذوف
    POST: /api/comments/restore/{id}/
    """
    permission_classes = [IsAdminOrReadOnly]

    def post(self, request, id):
        try:
            comment = Comments.objects.get(id=id, deleted_at__isnull=False)
            comment.deleted_at = None
            comment.save()
            
            serializer = CommentsDetailSerializer(comment)
            return Response({
                "message": "comment restored successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Comments.DoesNotExist:
            return Response({
                "message": "comment not found or not deleted"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ BULK DELETE ============
class CommentBulkDeleteView(APIView):
    """
    حذف ناعم لمجموعة تعليقات
    DELETE: /api/comments/bulk-delete/
    """
    permission_classes = [IsAdminOrReadOnly]

    def delete(self, request):
        comment_ids = request.data.get('ids', [])
        
        if not comment_ids:
            return Response({
                "message": "please provide ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(comment_ids, list):
            return Response({
                "message": "ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        deleted_count = Comments.objects.filter(
            id__in=comment_ids, 
            deleted_at__isnull=True
        ).update(deleted_at=timezone.now())
        
        if deleted_count == 0:
            return Response({
                "message": "no comments were deleted. they may already be deleted or not exist."
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "message": f"{deleted_count} out of {len(comment_ids)} comments deleted successfully"
        }, status=status.HTTP_200_OK)


# ============ BULK RESTORE ============
class CommentBulkRestoreView(APIView):
    """
    استعادة مجموعة تعليقات محذوفة
    POST: /api/comments/bulk-restore/
    """
    permission_classes = [IsAdminOrReadOnly]

    def post(self, request):
        comment_ids = request.data.get('ids', [])
        
        if not comment_ids:
            return Response({
                "message": "please provide ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(comment_ids, list):
            return Response({
                "message": "ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        restored_count = Comments.objects.filter(
            id__in=comment_ids, 
            deleted_at__isnull=False
        ).update(deleted_at=None)
        
        if restored_count == 0:
            return Response({
                "message": "no comments were restored. they may not be deleted or not exist."
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "message": f"{restored_count} out of {len(comment_ids)} comments restored successfully"
        }, status=status.HTTP_200_OK)


# ============ GET DELETED COMMENTS ============
class CommentDeletedListView(generics.ListAPIView):
    """
    عرض قائمة التعليقات المحذوفة
    GET: /api/comments/deleted/
    """
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = CommentsDeletedListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['post', 'name', 'email']
    search_fields = ['name', 'email', 'comment']
    ordering_fields = ['deleted_at', 'created_at']
    ordering = ['-deleted_at']
    pagination_class = CompactPagination
    
    def get_queryset(self):
        return Comments.objects.filter(deleted_at__isnull=False)


# ============ APPROVE / UNAPPROVE COMMENT ============
class CommentApproveView(APIView):
    """
    الموافقة على تعليق
    POST: /api/comments/approve/{id}/
    """
    permission_classes = [IsAdminOrReadOnly]
    
    def post(self, request, id):
        try:
            comment = Comments.objects.get(id=id, deleted_at__isnull=True)
            comment.is_approved = True
            comment.save()
            
            serializer = CommentsDetailSerializer(comment)
            return Response({
                "message": "comment approved successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Comments.DoesNotExist:
            return Response({
                "message": "comment not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class CommentUnapproveView(APIView):
    """
    إلغاء الموافقة على تعليق
    POST: /api/comments/unapprove/{id}/
    """
    permission_classes = [IsAdminOrReadOnly]
    
    def post(self, request, id):
        try:
            comment = Comments.objects.get(id=id, deleted_at__isnull=True)
            comment.is_approved = False
            comment.save()
            
            serializer = CommentsDetailSerializer(comment)
            return Response({
                "message": "comment unapproved successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Comments.DoesNotExist:
            return Response({
                "message": "comment not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ GET COMMENTS BY POST ============
class CommentsByPostView(generics.ListAPIView):
   
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = CommentsListSerializer
    pagination_class = CompactPagination
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]  
    ordering_fields = ['created_at', 'name', 'is_approved']
    ordering = ['-created_at']
    filterset_fields = ['is_approved']  

    
    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        queryset = Comments.objects.filter(
            post_id=post_id,
            deleted_at__isnull=True
        )
        
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_approved=True)
        
        return queryset