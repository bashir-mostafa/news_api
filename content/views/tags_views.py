from rest_framework import generics, status, filters, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from content.pagination import CompactPagination
from content.models import Tags
from content.serializers import (
    TagsSerializer, 
    TagsCreateUpdateSerializer, 
    TagsDetailSerializer,
    TagsListSerializer
)
from datetime import datetime
from django.utils import timezone
# ============ LIST & CREATE ============
class TagListCreateView(generics.ListCreateAPIView):
    queryset = Tags.objects.filter(deleted_at__isnull=True)
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    pagination_class = CompactPagination
    search_fields = ['name_ar', 'name_ku', 'name_en']
    ordering_fields = ['created_at', 'name_ar', 'name_en', 'name_ku']
    ordering = ['-created_at'] 
    

    def get_queryset(self):
        queryset = super().get_queryset()
        
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
            return TagsListSerializer
        return TagsCreateUpdateSerializer
    
    def perform_create(self, serializer):
        serializer.save()
    
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            tag = Tags.objects.get(id=serializer.instance.id)
            detail_serializer = TagsDetailSerializer(tag)
            
            return Response({
                "message": "tag created successfully",
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
                "message": "get all tags successfully",
                "count": queryset.count(),
                "data": serializer.data
            })
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ RETRIEVE, UPDATE, DELETE ============
class TagRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):

    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'id'  
    
    def get_queryset(self):
        return Tags.objects.filter(deleted_at__isnull=True)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return TagsCreateUpdateSerializer
        return TagsDetailSerializer
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            
            return Response({
                "message": "get tag details successfully",
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
            detail_serializer = TagsDetailSerializer(updated_instance)
            
            return Response({
                "message": "tag updated successfully",
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
                "message": "tag deleted successfully"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ HARD DELETE ============
class TagHardDeleteView(generics.DestroyAPIView):

    permission_classes = [IsAuthenticated, IsAdminUser] 
    lookup_field = 'id'  

    def get_queryset(self):
        return Tags.objects.all()
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            tag_name = instance.slug
            instance.delete()
            
            return Response({
                "message": f"tag '{tag_name}' deleted permanently successfully"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class TagBulkHardDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request):
        tag_ids = request.data.get('ids', [])
        
        if not tag_ids:
            return Response({
                "message": "please provide ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(tag_ids, list):
            return Response({
                "message": "ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get tags to return their names in response
        tags = Tags.objects.filter(id__in=tag_ids)
        found_ids = list(tags.values_list('id', flat=True))
        
        if not found_ids:
            return Response({
                "message": "no tags found with the provided ids"
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Store tag names for response message (using slug as identifier)
        tag_names = list(tags.values_list('slug', flat=True))
        deleted_count = len(found_ids)
        
        # Permanent delete
        tags.delete()
        
        return Response({
            "message": f"{deleted_count} out of {len(tag_ids)} tags deleted permanently successfully",
            "deleted_ids": found_ids,
            "deleted_names": tag_names
        }, status=status.HTTP_200_OK)

# ============ RESTORE DELETED ============
class TagRestoreView(APIView):

    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, id):
        try:
            tag = Tags.objects.get(id=id, deleted_at__isnull=False)
            tag.deleted_at = None
            tag.save()
            
            serializer = TagsDetailSerializer(tag)
            return Response({
                "message": "tag restored successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Tags.DoesNotExist:
            return Response({
                "message": "tag not found or not deleted"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ BULK DELETE ============
class TagBulkDeleteView(APIView):

    permission_classes = [IsAuthenticatedOrReadOnly]

    def delete(self, request):
        tag_ids = request.data.get('tag_ids', [])
        
        if not tag_ids:
            return Response({
                "message": "please provide tag_ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(tag_ids, list):
            return Response({
                "message": "tag_ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        deleted_count = Tags.objects.filter(
            id__in=tag_ids, 
            deleted_at__isnull=True
        ).update(deleted_at=timezone.now())
        
        if deleted_count == 0:
            return Response({
                "message": "no tags were deleted. they may already be deleted or not exist."
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "message": f"{deleted_count} out of {len(tag_ids)} tags deleted successfully"
        }, status=status.HTTP_200_OK)


# ============ BULK RESTORE ============
class TagBulkRestoreView(APIView):

    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request):
        tag_ids = request.data.get('tag_ids', [])
        
        if not tag_ids:
            return Response({
                "message": "please provide tag_ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(tag_ids, list):
            return Response({
                "message": "tag_ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        restored_count = Tags.objects.filter(
            id__in=tag_ids, 
            deleted_at__isnull=False
        ).update(deleted_at=None)
        
        if restored_count == 0:
            return Response({
                "message": "no tags were restored. they may not be deleted or not exist."
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "message": f"{restored_count} out of {len(tag_ids)} tags restored successfully"
        }, status=status.HTTP_200_OK)