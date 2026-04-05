from datetime import datetime
from django.utils import timezone
from rest_framework import generics, status, filters, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from content.pagination import CompactPagination
from content.models import Authors
from content.serializers import (
    AuthorsSerializer,
    AuthorsCreateUpdateSerializer,
    AuthorsDetailSerializer,
    AuthorsListSerializer
)

# ============ LIST & CREATE ============
class AuthorListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['id']
    pagination_class = CompactPagination
    search_fields = ['full_name', 'email', 'bio', 'slug']
    ordering_fields = ['created_at', 'full_name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Authors.objects.filter(deleted_at__isnull=True)
        
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
        
        filter_fields = {
            'full_name': 'full_name',
            'email': 'email',
            'slug': 'slug',
            'bio': 'bio'
        }
        
        for param, field in filter_fields.items():
            value = self.request.query_params.get(param)
            if value:
                queryset = queryset.filter(**{f'{field}__icontains': value})
        
        return queryset
        
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return AuthorsListSerializer
        return AuthorsCreateUpdateSerializer
    
    def perform_create(self, serializer):
        serializer.save()
    
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            author = Authors.objects.get(id=serializer.instance.id)
            detail_serializer = AuthorsDetailSerializer(author)
            
            return Response({
                "message": "author created successfully",
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
                "message": "get all authors successfully",
                "count": queryset.count(),
                "data": serializer.data
            })
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ RETRIEVE, UPDATE, DELETE ============
class AuthorRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'id'
    
    def get_queryset(self):
        return Authors.objects.filter(deleted_at__isnull=True)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return AuthorsCreateUpdateSerializer
        return AuthorsDetailSerializer
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            
            return Response({
                "message": "get author details successfully",
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
            detail_serializer = AuthorsDetailSerializer(updated_instance)
            
            return Response({
                "message": "author updated successfully",
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
                "message": "author deleted successfully"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ HARD DELETE ============
class AuthorHardDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'id'
    
    def get_queryset(self):
        return Authors.objects.all()
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            author_name = instance.full_name
            instance.delete()
            
            return Response({
                "message": f"author '{author_name}' deleted permanently successfully"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class AuthorBulkHardDeleteView(APIView):

    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request):
        author_ids = request.data.get('ids', [])
        
        if not author_ids:
            return Response({
                "message": "please provide ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(author_ids, list):
            return Response({
                "message": "ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get authors to return their names in response
        authors = Authors.objects.filter(id__in=author_ids)
        found_ids = list(authors.values_list('id', flat=True))
        
        if not found_ids:
            return Response({
                "message": "no authors found with the provided ids"
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Store author names for response message
        author_names = list(authors.values_list('full_name', flat=True))
        deleted_count = len(found_ids)
        
        # Permanent delete
        authors.delete()
        
        return Response({
            "message": f"{deleted_count} out of {len(author_ids)} authors deleted permanently successfully",
            "deleted_ids": found_ids,
            "deleted_names": author_names
        }, status=status.HTTP_200_OK)

# ============ RESTORE DELETED ============
class AuthorRestoreView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def post(self, request, id):
        try:
            author = Authors.objects.get(id=id, deleted_at__isnull=False)
            author.deleted_at = None
            author.save()
            
            serializer = AuthorsDetailSerializer(author)
            return Response({
                "message": "author restored successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Authors.DoesNotExist:
            return Response({
                "message": "author not found or not deleted"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ BULK DELETE ============
class AuthorBulkDeleteView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def delete(self, request):
        author_ids = request.data.get('ids', [])
        
        if not author_ids:
            return Response({
                "message": "please provide author_ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(author_ids, list):
            return Response({
                "message": "author_ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        deleted_count = Authors.objects.filter(
            id__in=author_ids, 
            deleted_at__isnull=True
        ).update(deleted_at=timezone.now())
        
        if deleted_count == 0:
            return Response({
                "message": "no authors were deleted. they may already be deleted or not exist."
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "message": f"{deleted_count} out of {len(author_ids)} authors deleted successfully"
        }, status=status.HTTP_200_OK)


# ============ BULK RESTORE ============
class AuthorBulkRestoreView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request):
        author_ids = request.data.get('ids', [])
        
        if not author_ids:
            return Response({
                "message": "please provide author_ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(author_ids, list):
            return Response({
                "message": "author_ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        restored_count = Authors.objects.filter(
            id__in=author_ids, 
            deleted_at__isnull=False
        ).update(deleted_at=None)
        
        if restored_count == 0:
            return Response({
                "message": "no authors were restored. they may not be deleted or not exist."
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "message": f"{restored_count} out of {len(author_ids)} authors restored successfully"
        }, status=status.HTTP_200_OK)