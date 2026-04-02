# content/views/posts_views.py
from rest_framework import generics, status, filters, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from content.pagination import CompactPagination
from content.models import Posts, ContentType, Language
from content.serializers import (
    PostsSerializer,
    PostsCreateUpdateSerializer,
    PostsDetailSerializer,
    PostsListSerializer,
    PostsDeletedListSerializer
)

# ============ LIST & CREATE ============
class PostListCreateView(generics.ListCreateAPIView):
    """
    عرض قائمة المقالات وإنشاء مقال جديد
    GET: /api/posts/
    POST: /api/posts/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['id', 'is_published', 'content_type', 'language', 'author', 'category']
    pagination_class = CompactPagination
    search_fields = ['title', 'excerpt', 'content', 'meta_title', 'meta_description']
    ordering_fields = ['created_at', 'published_at', 'view_count', 'title', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Posts.objects.filter(deleted_at__isnull=True)
        id_ne = self.request.query_params.get('id_ne')
        if id_ne:
            try:
                queryset = queryset.exclude(id=int(id_ne))
            except ValueError:
                pass
        content_type = self.request.query_params.get('content_type')
        if content_type:
            queryset = queryset.filter(content_type=content_type)
        
        language = self.request.query_params.get('language')
        if language:
            queryset = queryset.filter(language=language)
        
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                is_published=True,
                published_at__lte=timezone.now()
            )
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PostsListSerializer
        return PostsCreateUpdateSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            post = Posts.objects.get(id=serializer.instance.id)
            detail_serializer = PostsDetailSerializer(post, context={'request': request})
            
            return Response({
                "message": "post created successfully",
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
                "message": "get all posts successfully",
                "count": queryset.count(),
                "data": serializer.data
            })
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ RETRIEVE, UPDATE, DELETE ============
class PostRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """
    عرض وتحديث وحذف مقال محدد
    GET: /api/posts/{id}/
    PUT: /api/posts/{id}/
    PATCH: /api/posts/{id}/
    DELETE: /api/posts/{id}/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'id'
    
    def get_queryset(self):
        queryset = Posts.objects.filter(deleted_at__isnull=True)
        
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                is_published=True,
                published_at__lte=timezone.now()
            )
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PostsCreateUpdateSerializer
        return PostsDetailSerializer
    
    def get_serializer_context(self):
        """تمرير الـ request إلى الـ serializer للصور"""
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            
            # زيادة عدد المشاهدات
            instance.view_count += 1
            instance.save(update_fields=['view_count'])
            
            serializer = self.get_serializer(instance, context={'request': request})
            
            return Response({
                "message": "get post details successfully",
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
            detail_serializer = PostsDetailSerializer(updated_instance, context={'request': request})
            
            return Response({
                "message": "post updated successfully",
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
                "message": "post deleted successfully"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ HARD DELETE ============
class PostHardDeleteView(generics.DestroyAPIView):
    """
    حذف نهائي لمقال (للمشرفين فقط)
    DELETE: /api/posts/hard-delete/{id}/
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'id'
    queryset = Posts.objects.all()
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            post_title = instance.title
            instance.delete()
            
            return Response({
                "message": f"post '{post_title}' deleted permanently successfully"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class PostBulkHardDeleteView(APIView):

    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request):
        post_ids = request.data.get('ids', [])
        
        if not post_ids:
            return Response({
                "message": "please provide ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(post_ids, list):
            return Response({
                "message": "ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        posts = Posts.objects.filter(id__in=post_ids)
        found_ids = list(posts.values_list('id', flat=True))
        
        if not found_ids:
            return Response({
                "message": "no posts found with the provided ids"
            }, status=status.HTTP_404_NOT_FOUND)
        
        post_titles = list(posts.values_list('title', flat=True))
        deleted_count = len(found_ids)
        
        posts.delete()
        
        return Response({
            "message": f"{deleted_count} out of {len(post_ids)} posts deleted permanently successfully",
            "deleted_ids": found_ids,
            "deleted_titles": post_titles
        }, status=status.HTTP_200_OK)


# ============ RESTORE DELETED ============
class PostRestoreView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def post(self, request, id):
        try:
            post = Posts.objects.get(id=id, deleted_at__isnull=False)
            post.deleted_at = None
            post.save()
            
            serializer = PostsDetailSerializer(post, context={'request': request})
            return Response({
                "message": "post restored successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Posts.DoesNotExist:
            return Response({
                "message": "post not found or not deleted"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ BULK DELETE ============
class PostBulkDeleteView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def delete(self, request):
        post_ids = request.data.get('ids', [])
        
        if not post_ids:
            return Response({
                "message": "please provide ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(post_ids, list):
            return Response({
                "message": "ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        deleted_count = Posts.objects.filter(
            id__in=post_ids, 
            deleted_at__isnull=True
        ).update(deleted_at=timezone.now())
        
        if deleted_count == 0:
            return Response({
                "message": "no posts were deleted. they may already be deleted or not exist."
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "message": f"{deleted_count} out of {len(post_ids)} posts deleted successfully"
        }, status=status.HTTP_200_OK)


# ============ BULK RESTORE ============
class PostBulkRestoreView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request):
        post_ids = request.data.get('ids', [])
        
        if not post_ids:
            return Response({
                "message": "please provide ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(post_ids, list):
            return Response({
                "message": "ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        restored_count = Posts.objects.filter(
            id__in=post_ids, 
            deleted_at__isnull=False
        ).update(deleted_at=None)
        
        if restored_count == 0:
            return Response({
                "message": "no posts were restored. they may not be deleted or not exist."
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "message": f"{restored_count} out of {len(post_ids)} posts restored successfully"
        }, status=status.HTTP_200_OK)


# ============ GET DELETED POSTS ============
class PostDeletedListView(generics.ListAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = PostsDeletedListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['content_type', 'language', 'author', 'category']
    search_fields = ['title', 'excerpt']
    ordering_fields = ['deleted_at', 'created_at']
    ordering = ['-deleted_at']
    pagination_class = CompactPagination
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    
    def get_queryset(self):
        return Posts.objects.filter(deleted_at__isnull=False)


# ============ POST STATISTICS ============
class PostStatisticsView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get(self, request):
        total_posts = Posts.objects.filter(deleted_at__isnull=True).count()
        published_posts = Posts.objects.filter(
            is_published=True,
            deleted_at__isnull=True,
            published_at__lte=timezone.now()
        ).count()
        draft_posts = Posts.objects.filter(
            is_published=False,
            deleted_at__isnull=True
        ).count()
        deleted_posts = Posts.objects.filter(deleted_at__isnull=False).count()
        
        content_type_stats = {}
        for content_type in ContentType.choices:
            count = Posts.objects.filter(
                content_type=content_type[0],
                deleted_at__isnull=True,
                is_published=True
            ).count()
            content_type_stats[content_type[1]] = count
        
        language_stats = {}
        for language in Language.choices:
            count = Posts.objects.filter(
                language=language[0],
                deleted_at__isnull=True,
                is_published=True
            ).count()
            language_stats[language[1]] = count
        
        return Response({
            "message": "post statistics retrieved successfully",
            "data": {
                "total_posts": total_posts,
                "published_posts": published_posts,
                "draft_posts": draft_posts,
                "deleted_posts": deleted_posts,
                "by_content_type": content_type_stats,
                "by_language": language_stats,
                "total_views": Posts.objects.aggregate(total=models.Sum('view_count'))['total'] or 0
            }
        })


# ============ PUBLISH / UNPUBLISH POST ============
class PostPublishView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def post(self, request, id):
        try:
            post = Posts.objects.get(id=id, deleted_at__isnull=True)
            post.is_published = True
            if not post.published_at:
                post.published_at = timezone.now()
            post.save()
            
            serializer = PostsDetailSerializer(post, context={'request': request})
            return Response({
                "message": "post published successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Posts.DoesNotExist:
            return Response({
                "message": "post not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class PostUnpublishView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def post(self, request, id):
        try:
            post = Posts.objects.get(id=id, deleted_at__isnull=True)
            post.is_published = False
            post.save()
            
            serializer = PostsDetailSerializer(post, context={'request': request})
            return Response({
                "message": "post unpublished successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Posts.DoesNotExist:
            return Response({
                "message": "post not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ INCREMENT VIEW COUNT ============
class PostIncrementViewView(APIView):
    permission_classes = []  # Allow anyone to increment view count
    
    def post(self, request, id):
        try:
            post = Posts.objects.get(id=id, deleted_at__isnull=True)
            post.view_count += 1
            post.save(update_fields=['view_count'])
            
            return Response({
                "message": "view counted successfully",
                "view_count": post.view_count
            }, status=status.HTTP_200_OK)
            
        except Posts.DoesNotExist:
            return Response({
                "message": "post not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ GET POSTS BY ID ============
class PostByIdView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get(self, request, id):
        try:
            queryset = Posts.objects.filter(id=id, deleted_at__isnull=True)
            
            if not request.user.is_staff:
                queryset = queryset.filter(
                    is_published=True,
                    published_at__lte=timezone.now()
                )
            
            post = queryset.first()
            if not post:
                return Response({
                    "message": "post not found"
                }, status=status.HTTP_404_NOT_FOUND)
            
            post.view_count += 1
            post.save(update_fields=['view_count'])
            
            serializer = PostsDetailSerializer(post, context={'request': request})
            return Response({
                "message": "post retrieved successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)