# content/views/events_views.py
from rest_framework import generics, status, filters, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from content.pagination import CompactPagination
from content.models import Events
from content.serializers import (
    EventsSerializer,
    EventsCreateUpdateSerializer,
    EventsDetailSerializer,
    EventsListSerializer,
    EventsDeletedListSerializer
)

# ============ LIST & CREATE ============
class EventListCreateView(generics.ListCreateAPIView):
    """
    عرض قائمة الأحداث وإنشاء حدث جديد
    GET: /api/events/
    POST: /api/events/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['id', 'post', 'event_type', 'location']
    pagination_class = CompactPagination
    search_fields = ['event_type', 'location']
    ordering_fields = ['event_date', 'created_at', 'attendees_count']
    ordering = ['-event_date']
    
    def get_queryset(self):
        queryset = Events.objects.filter(deleted_at__isnull=True)
        
        # تصفية حسب المقال
        post_id = self.request.query_params.get('post')
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        
        # تصفية حسب نوع الحدث
        event_type = self.request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # تصفية حسب الأحداث القادمة أو الماضية
        status = self.request.query_params.get('status')
        if status == 'upcoming':
            queryset = queryset.filter(event_date__gt=timezone.now())
        elif status == 'past':
            queryset = queryset.filter(event_date__lt=timezone.now())
        
        # للمستخدمين غير المسجلين، عرض الأحداث القادمة فقط (اختياري)
        if not self.request.user.is_staff:
            queryset = queryset.filter(event_date__gt=timezone.now())
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return EventsListSerializer
        return EventsCreateUpdateSerializer
    
    def perform_create(self, serializer):
        serializer.save()
    
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            event = Events.objects.get(id=serializer.instance.id)
            detail_serializer = EventsDetailSerializer(event)
            
            return Response({
                "message": "event created successfully",
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
                "message": "get all events successfully",
                "count": queryset.count(),
                "data": serializer.data
            })
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ RETRIEVE, UPDATE, DELETE ============
class EventRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """
    عرض وتحديث وحذف حدث محدد
    GET: /api/events/{id}/
    PUT: /api/events/{id}/
    PATCH: /api/events/{id}/
    DELETE: /api/events/{id}/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'id'
    
    def get_queryset(self):
        queryset = Events.objects.filter(deleted_at__isnull=True)
        
        # للمستخدمين غير المسجلين، عرض الأحداث القادمة فقط
        if not self.request.user.is_staff:
            queryset = queryset.filter(event_date__gt=timezone.now())
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return EventsCreateUpdateSerializer
        return EventsDetailSerializer
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            
            return Response({
                "message": "get event details successfully",
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
            detail_serializer = EventsDetailSerializer(updated_instance)
            
            return Response({
                "message": "event updated successfully",
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
                "message": "event deleted successfully"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ HARD DELETE ============
class EventHardDeleteView(generics.DestroyAPIView):
    """
    حذف نهائي لحدث (للمشرفين فقط)
    DELETE: /api/events/hard-delete/{id}/
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'id'
    queryset = Events.objects.all()
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            event_id = instance.id
            instance.delete()
            
            return Response({
                "message": f"event '{event_id}' deleted permanently successfully"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class EventBulkHardDeleteView(APIView):
    """
    حذف نهائي لمجموعة أحداث (للمشرفين فقط)
    DELETE: /api/events/bulk-hard-delete/
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request):
        event_ids = request.data.get('ids', [])
        
        if not event_ids:
            return Response({
                "message": "please provide ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(event_ids, list):
            return Response({
                "message": "ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        events = Events.objects.filter(id__in=event_ids)
        found_ids = list(events.values_list('id', flat=True))
        
        if not found_ids:
            return Response({
                "message": "no events found with the provided ids"
            }, status=status.HTTP_404_NOT_FOUND)
        
        deleted_count = len(found_ids)
        events.delete()
        
        return Response({
            "message": f"{deleted_count} out of {len(event_ids)} events deleted permanently successfully",
            "deleted_ids": found_ids
        }, status=status.HTTP_200_OK)


# ============ RESTORE DELETED ============
class EventRestoreView(APIView):
    """
    استعادة حدث محذوف
    POST: /api/events/restore/{id}/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, id):
        try:
            event = Events.objects.get(id=id, deleted_at__isnull=False)
            event.deleted_at = None
            event.save()
            
            serializer = EventsDetailSerializer(event)
            return Response({
                "message": "event restored successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Events.DoesNotExist:
            return Response({
                "message": "event not found or not deleted"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ BULK DELETE ============
class EventBulkDeleteView(APIView):
    """
    حذف ناعم لمجموعة أحداث
    DELETE: /api/events/bulk-delete/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def delete(self, request):
        event_ids = request.data.get('ids', [])
        
        if not event_ids:
            return Response({
                "message": "please provide ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(event_ids, list):
            return Response({
                "message": "ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        deleted_count = Events.objects.filter(
            id__in=event_ids, 
            deleted_at__isnull=True
        ).update(deleted_at=timezone.now())
        
        if deleted_count == 0:
            return Response({
                "message": "no events were deleted. they may already be deleted or not exist."
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "message": f"{deleted_count} out of {len(event_ids)} events deleted successfully"
        }, status=status.HTTP_200_OK)


# ============ BULK RESTORE ============
class EventBulkRestoreView(APIView):
    """
    استعادة مجموعة أحداث محذوفة
    POST: /api/events/bulk-restore/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request):
        event_ids = request.data.get('ids', [])
        
        if not event_ids:
            return Response({
                "message": "please provide ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(event_ids, list):
            return Response({
                "message": "ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        restored_count = Events.objects.filter(
            id__in=event_ids, 
            deleted_at__isnull=False
        ).update(deleted_at=None)
        
        if restored_count == 0:
            return Response({
                "message": "no events were restored. they may not be deleted or not exist."
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "message": f"{restored_count} out of {len(event_ids)} events restored successfully"
        }, status=status.HTTP_200_OK)


# ============ GET DELETED EVENTS ============
class EventDeletedListView(generics.ListAPIView):
    """
    عرض قائمة الأحداث المحذوفة
    GET: /api/events/deleted/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = EventsDeletedListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['post', 'event_type', 'location']
    search_fields = ['event_type', 'location']
    ordering_fields = ['deleted_at', 'event_date', 'created_at']
    ordering = ['-deleted_at']
    pagination_class = CompactPagination
    
    def get_queryset(self):
        return Events.objects.filter(deleted_at__isnull=False)


# ============ INCREMENT ATTENDEES COUNT ============
class EventIncrementAttendeesView(APIView):
    """
    زيادة عدد الحضور في الحدث
    POST: /api/events/increment-attendees/{id}/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def post(self, request, id):
        try:
            event = Events.objects.get(id=id, deleted_at__isnull=True)
            
            # التحقق من أن الحدث لم يمض
            if event.event_date < timezone.now():
                return Response({
                    "message": "Cannot increment attendees for past events"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            event.attendees_count += 1
            event.save()
            
            serializer = EventsDetailSerializer(event)
            return Response({
                "message": "Attendees count incremented successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Events.DoesNotExist:
            return Response({
                "message": "Event not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ DECREMENT ATTENDEES COUNT ============
class EventDecrementAttendeesView(APIView):
    """
    إنقاص عدد الحضور في الحدث
    POST: /api/events/decrement-attendees/{id}/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def post(self, request, id):
        try:
            event = Events.objects.get(id=id, deleted_at__isnull=True)
            
            if event.event_date < timezone.now():
                return Response({
                    "message": "Cannot decrement attendees for past events"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if event.attendees_count > 0:
                event.attendees_count -= 1
                event.save()
            
            serializer = EventsDetailSerializer(event)
            return Response({
                "message": "Attendees count decremented successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Events.DoesNotExist:
            return Response({
                "message": "Event not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ GET EVENTS BY POST ============
class EventsByPostView(generics.ListAPIView):
    """
    عرض أحداث مقال محدد
    GET: /api/events/by-post/{post_id}/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = EventsListSerializer
    pagination_class = CompactPagination
    
    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        queryset = Events.objects.filter(
            post_id=post_id,
            deleted_at__isnull=True
        )
        
        # للمستخدمين غير المسجلين، عرض الأحداث القادمة فقط
        if not self.request.user.is_staff:
            queryset = queryset.filter(event_date__gt=timezone.now())
        
        return queryset