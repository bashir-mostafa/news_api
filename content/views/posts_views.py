# content/views/posts_views.py
from datetime import datetime
import json
from django.utils import timezone
from rest_framework import generics, status, filters, serializers
from rest_framework.response import Response
from news_api.permission import IsAdmin, IsAdminOrReadOnly, AllowAny
from rest_framework.views import APIView
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from content.pagination import CompactPagination
from content.models import Posts, ContentType, Language
from django.db.models import Q
from content.serializers import (
    PostsSerializer,
    PostsCreateUpdateSerializer,
    PostsDetailSerializer,
    PostsListSerializer,
    PostsDeletedListSerializer
)

# ============ LIST & CREATE ============
class PostListCreateView(generics.ListCreateAPIView):

    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    pagination_class = CompactPagination
    search_fields = ['title', 'excerpt', 'content', 'meta_title', 'meta_description']
    ordering_fields = ['created_at', 'published_at', 'view_count', 'title', 'updated_at']
    ordering = ['-created_at']
    
    def _parse_value(self, value):
        if not value:
            return []
        
        if isinstance(value, str) and value.strip().startswith('[') and value.strip().endswith(']'):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
        
        if isinstance(value, str) and ',' in value:
            return value.split(',')
        
        return [value] if value else []
    
    def get_queryset(self):
        queryset = Posts.objects.filter(deleted_at__isnull=True)

        id_ne = self.request.query_params.get('id_ne')
        if id_ne:
            try:
                queryset = queryset.exclude(id=int(id_ne))
            except ValueError:
                pass

        # ===== 2. content_type  =====
        content_type = self.request.query_params.get('content_type')
        content_type_or = self.request.query_params.get('content_type_or')
        content_type_multi = self.request.query_params.get('content_type_multi')
        
        content_type_values = []
        
        if content_type:
            content_type_values.extend(self._parse_value(content_type))
        if content_type_or:
            content_type_values.extend(self._parse_value(content_type_or))
        if content_type_multi:
            content_type_values.extend(self._parse_value(content_type_multi))
        
        content_type_array = self.request.query_params.getlist('content_type')
        if len(content_type_array) > 1:
            for val in content_type_array:
                content_type_values.extend(self._parse_value(val))
        
        content_type_values = list(dict.fromkeys(content_type_values))
        
        if content_type_values:
            if content_type_or is not None:
                # OR logic
                q_content_type = Q()
                for ct in content_type_values:
                    q_content_type |= Q(content_type=ct)
                queryset = queryset.filter(q_content_type)
            else:
                # IN logic
                if len(content_type_values) == 1:
                    queryset = queryset.filter(content_type=content_type_values[0])
                else:
                    queryset = queryset.filter(content_type__in=content_type_values)
            

        # ===== 3. language  =====
        language = self.request.query_params.get('language')
        language_or = self.request.query_params.get('language_or')
        language_multi = self.request.query_params.get('language_multi')
        
        language_values = []
        
        if language:
            language_values.extend(self._parse_value(language))
        if language_or:
            language_values.extend(self._parse_value(language_or))
        if language_multi:
            language_values.extend(self._parse_value(language_multi))
        
        language_array = self.request.query_params.getlist('language')
        if len(language_array) > 1:
            for val in language_array:
                language_values.extend(self._parse_value(val))
        
        language_values = list(dict.fromkeys(language_values))
        
        if language_values:
            if language_or is not None:
                q_language = Q()
                for lang in language_values:
                    q_language |= Q(language=lang)
                queryset = queryset.filter(q_language)
            else:
                if len(language_values) == 1:
                    queryset = queryset.filter(language=language_values[0])
                else:
                    queryset = queryset.filter(language__in=language_values)

        # ===== 5. title  =====
        title = self.request.query_params.get('title')
        title_or = self.request.query_params.get('title_or')
        title_multi = self.request.query_params.get('title_multi')
        
        title_values = []
        
        if title:
            title_values.extend(self._parse_value(title))
        if title_or:
            title_values.extend(self._parse_value(title_or))
        if title_multi:
            title_values.extend(self._parse_value(title_multi))
        
        title_array = self.request.query_params.getlist('title')
        if len(title_array) > 1:
            for val in title_array:
                title_values.extend(self._parse_value(val))
        
        title_values = list(dict.fromkeys(title_values))
        
        if title_values:
            q_title = Q()
            for t in title_values:
                q_title |= Q(title__icontains=t)
            queryset = queryset.filter(q_title)
        
        # ===== 6. excerpt  =====
        excerpt = self.request.query_params.get('excerpt')
        excerpt_or = self.request.query_params.get('excerpt_or')
        excerpt_multi = self.request.query_params.get('excerpt_multi')
        
        excerpt_values = []
        
        if excerpt:
            excerpt_values.extend(self._parse_value(excerpt))
        if excerpt_or:
            excerpt_values.extend(self._parse_value(excerpt_or))
        if excerpt_multi:
            excerpt_values.extend(self._parse_value(excerpt_multi))
        
        excerpt_array = self.request.query_params.getlist('excerpt')
        if len(excerpt_array) > 1:
            for val in excerpt_array:
                excerpt_values.extend(self._parse_value(val))
        
        excerpt_values = list(dict.fromkeys(excerpt_values))
        
        if excerpt_values:
            q_excerpt = Q()
            for e in excerpt_values:
                q_excerpt |= Q(excerpt__icontains=e)
            queryset = queryset.filter(q_excerpt)
        

        # ===== 7. category  =====
        category = self.request.query_params.get('category')
        category_or = self.request.query_params.get('category_or')
        category_multi = self.request.query_params.get('category_multi')
        
        category_values = []
        
        if category:
            category_values.extend(self._parse_value(category))
        if category_or:
            category_values.extend(self._parse_value(category_or))
        if category_multi:
            category_values.extend(self._parse_value(category_multi))
        
        category_array = self.request.query_params.getlist('category')
        if len(category_array) > 1:
            for val in category_array:
                category_values.extend(self._parse_value(val))
        
        category_values_int = []
        for val in category_values:
            try:
                category_values_int.append(int(val))
            except (ValueError, TypeError):
                pass
        
        category_values_int = list(dict.fromkeys(category_values_int))
        
        if category_values_int:
            if category_or is not None:
                q_category = Q()
                for cat in category_values_int:
                    q_category |= Q(category_id=cat)
                queryset = queryset.filter(q_category)
            else:
                if len(category_values_int) == 1:
                    queryset = queryset.filter(category_id=category_values_int[0])
                else:
                    queryset = queryset.filter(category_id__in=category_values_int)
        

        # ===== 8. tags  =====
        tags = self.request.query_params.get('tags')
        tags_or = self.request.query_params.get('tags_or')
        tags_multi = self.request.query_params.get('tags_multi')
        
        tags_values = []
        
        if tags:
            tags_values.extend(self._parse_value(tags))
        if tags_or:
            tags_values.extend(self._parse_value(tags_or))
        if tags_multi:
            tags_values.extend(self._parse_value(tags_multi))
        
        tags_array = self.request.query_params.getlist('tags')
        if len(tags_array) > 1:
            for val in tags_array:
                tags_values.extend(self._parse_value(val))
        
        tags_values_int = []
        for val in tags_values:
            try:
                tags_values_int.append(int(val))
            except (ValueError, TypeError):
                pass
        
        tags_values_int = list(dict.fromkeys(tags_values_int))
        
        if tags_values_int:
            if tags_or is not None:
                q_tags = Q()
                for tag in tags_values_int:
                    q_tags |= Q(tags__id=tag)
                queryset = queryset.filter(q_tags).distinct()
            else:
                if len(tags_values_int) == 1:
                    queryset = queryset.filter(tags__id=tags_values_int[0]).distinct()
                else:
                    queryset = queryset.filter(tags__id__in=tags_values_int).distinct()
        
        # ===== 9. author  =====
        author = self.request.query_params.get('author')
        author_or = self.request.query_params.get('author_or')
        author_multi = self.request.query_params.get('author_multi')
        
        author_values = []
        
        if author:
            author_values.extend(self._parse_value(author))
        if author_or:
            author_values.extend(self._parse_value(author_or))
        if author_multi:
            author_values.extend(self._parse_value(author_multi))
        
        author_array = self.request.query_params.getlist('author')
        if len(author_array) > 1:
            for val in author_array:
                author_values.extend(self._parse_value(val))
        
        author_values_int = []
        for val in author_values:
            try:
                author_values_int.append(int(val))
            except (ValueError, TypeError):
                pass
        
        author_values_int = list(dict.fromkeys(author_values_int))
        
        if author_values_int:
            if author_or is not None:
                q_author = Q()
                for auth in author_values_int:
                    q_author |= Q(author_id=auth)
                queryset = queryset.filter(q_author)
            else:
                if len(author_values_int) == 1:
                    queryset = queryset.filter(author_id=author_values_int[0])
                else:
                    queryset = queryset.filter(author_id__in=author_values_int)
        
        if language:
            queryset = queryset.filter(language=language)
        
        is_published = self.request.query_params.get('is_published')
        if is_published is not None:
            if is_published.lower() == 'true':
                queryset = queryset.filter(is_published=True)
            elif is_published.lower() == 'false':
                queryset = queryset.filter(is_published=False)
        
        created_at_gte = self.request.query_params.get('created_at_gte')
        created_at_lte = self.request.query_params.get('created_at_lte')
        
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
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'id'
    
    def get_queryset(self):
        queryset = Posts.objects.filter(deleted_at__isnull=True)
        
        if not hasattr(self.request.user, 'role') or self.request.user.role != "admin":
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
    permission_classes = [IsAdmin]
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

    permission_classes = [IsAdmin]

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
    permission_classes = [IsAdmin]
    
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
    permission_classes = [IsAdmin]

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
    permission_classes = [IsAdmin]

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
    permission_classes = [IsAdmin]
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
from django.db.models import Count, Sum, Q

class PostStatisticsView(APIView):
    permission_classes = [IsAdminOrReadOnly]
    
    def get_queryset(self):
        queryset = Posts.objects.filter(deleted_at__isnull=True)
        
        created_at_gte = self.request.query_params.get('created_at_gte')
        created_at_lte = self.request.query_params.get('created_at_lte')
        
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
        
        return queryset 
    
    def get(self, request):
        base_queryset = self.get_queryset()
        
        total_posts = base_queryset.count()
        published_posts = base_queryset.filter(
            is_published=True,
            published_at__lte=timezone.now()
        ).count()
        draft_posts = base_queryset.filter(is_published=False).count()
        deleted_posts = Posts.objects.filter(deleted_at__isnull=False).count()
        
        content_type_stats = dict(
            base_queryset.filter(is_published=True)
            .values('content_type')
            .annotate(count=Count('id'))
            .values_list('content_type', 'count')
        )
        
        for content_type, _ in ContentType.choices:
            if content_type not in content_type_stats:
                content_type_stats[content_type] = 0
        
        language_stats = dict(
            base_queryset.filter(is_published=True)
            .values('language')
            .annotate(count=Count('id'))
            .values_list('language', 'count')
        )
        
        language_names = dict(Language.choices)
        language_stats_named = {
            language_names.get(lang, lang): count 
            for lang, count in language_stats.items()
        }
        
        total_views = base_queryset.aggregate(total=Sum('view_count'))['total'] or 0
        
        return Response({
            "message": "post statistics retrieved successfully",
            "data": {
                "total_posts": total_posts,
                "published_posts": published_posts,
                "draft_posts": draft_posts,
                "deleted_posts": deleted_posts,
                "by_content_type": content_type_stats,
                "by_language": language_stats_named,
                "total_views": total_views
            }
        })


# ============ PUBLISH / UNPUBLISH POST ============
class PostPublishView(APIView):
    permission_classes = [IsAdmin]
    
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
    permission_classes = [IsAdmin]
    
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
    permission_classes = [AllowAny]  # Allow anyone to increment view count
    
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
    permission_classes = [IsAdminOrReadOnly]
    
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