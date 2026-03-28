# content/views/survey_options_views.py
from rest_framework import generics, status, filters, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from content.pagination import CompactPagination
from content.models import SurveyOptions, Surveys
from content.serializers import (
    SurveyOptionsSerializer,
    SurveyOptionsCreateUpdateSerializer,
    SurveyOptionsDetailSerializer,
    SurveyOptionsListSerializer,
    SurveyOptionsDeletedListSerializer
)

# ============ LIST & CREATE ============
class SurveyOptionListCreateView(generics.ListCreateAPIView):
    """
    عرض قائمة خيارات الاستبيان وإنشاء خيار جديد
    GET: /api/survey-options/
    POST: /api/survey-options/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['id', 'survey', 'vote_count']
    pagination_class = CompactPagination
    search_fields = ['option_text']
    ordering_fields = ['created_at', 'vote_count', 'option_text']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = SurveyOptions.objects.filter(deleted_at__isnull=True)
        
        # تصفية حسب الاستبيان
        survey_id = self.request.query_params.get('survey')
        if survey_id:
            queryset = queryset.filter(survey_id=survey_id)
        
        # للمستخدمين غير المسجلين، عرض فقط خيارات الاستبيانات النشطة
        if not self.request.user.is_staff:
            queryset = queryset.filter(survey__is_active=True, survey__deleted_at__isnull=True)
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SurveyOptionsListSerializer
        return SurveyOptionsCreateUpdateSerializer
    
    def perform_create(self, serializer):
        serializer.save()
    
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            option = SurveyOptions.objects.get(id=serializer.instance.id)
            detail_serializer = SurveyOptionsDetailSerializer(option)
            
            return Response({
                "message": "survey option created successfully",
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
                "message": "get all survey options successfully",
                "count": queryset.count(),
                "data": serializer.data
            })
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ RETRIEVE, UPDATE, DELETE ============
class SurveyOptionRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """
    عرض وتحديث وحذف خيار استبيان محدد
    GET: /api/survey-options/{id}/
    PUT: /api/survey-options/{id}/
    PATCH: /api/survey-options/{id}/
    DELETE: /api/survey-options/{id}/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'id'
    
    def get_queryset(self):
        queryset = SurveyOptions.objects.filter(deleted_at__isnull=True)
        
        # للمستخدمين غير المسجلين، عرض فقط خيارات الاستبيانات النشطة
        if not self.request.user.is_staff:
            queryset = queryset.filter(survey__is_active=True, survey__deleted_at__isnull=True)
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return SurveyOptionsCreateUpdateSerializer
        return SurveyOptionsDetailSerializer
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            
            return Response({
                "message": "get survey option details successfully",
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
            detail_serializer = SurveyOptionsDetailSerializer(updated_instance)
            
            return Response({
                "message": "survey option updated successfully",
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
                "message": "survey option deleted successfully"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ HARD DELETE ============
class SurveyOptionHardDeleteView(generics.DestroyAPIView):
    """
    حذف نهائي لخيار استبيان (للمشرفين فقط)
    DELETE: /api/survey-options/hard-delete/{id}/
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'id'
    queryset = SurveyOptions.objects.all()
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            option_id = instance.id
            instance.delete()
            
            return Response({
                "message": f"survey option '{option_id}' deleted permanently successfully"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class SurveyOptionBulkHardDeleteView(APIView):
    """
    حذف نهائي لمجموعة خيارات استبيان (للمشرفين فقط)
    DELETE: /api/survey-options/bulk-hard-delete/
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request):
        option_ids = request.data.get('ids', [])
        
        if not option_ids:
            return Response({
                "message": "please provide ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(option_ids, list):
            return Response({
                "message": "ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        options = SurveyOptions.objects.filter(id__in=option_ids)
        found_ids = list(options.values_list('id', flat=True))
        
        if not found_ids:
            return Response({
                "message": "no survey options found with the provided ids"
            }, status=status.HTTP_404_NOT_FOUND)
        
        deleted_count = len(found_ids)
        options.delete()
        
        return Response({
            "message": f"{deleted_count} out of {len(option_ids)} survey options deleted permanently successfully",
            "deleted_ids": found_ids
        }, status=status.HTTP_200_OK)


# ============ RESTORE DELETED ============
class SurveyOptionRestoreView(APIView):
    """
    استعادة خيار استبيان محذوف
    POST: /api/survey-options/restore/{id}/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, id):
        try:
            option = SurveyOptions.objects.get(id=id, deleted_at__isnull=False)
            option.deleted_at = None
            option.save()
            
            serializer = SurveyOptionsDetailSerializer(option)
            return Response({
                "message": "survey option restored successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except SurveyOptions.DoesNotExist:
            return Response({
                "message": "survey option not found or not deleted"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ BULK DELETE ============
class SurveyOptionBulkDeleteView(APIView):
    """
    حذف ناعم لمجموعة خيارات استبيان
    DELETE: /api/survey-options/bulk-delete/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def delete(self, request):
        option_ids = request.data.get('ids', [])
        
        if not option_ids:
            return Response({
                "message": "please provide ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(option_ids, list):
            return Response({
                "message": "ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        deleted_count = SurveyOptions.objects.filter(
            id__in=option_ids, 
            deleted_at__isnull=True
        ).update(deleted_at=timezone.now())
        
        if deleted_count == 0:
            return Response({
                "message": "no survey options were deleted. they may already be deleted or not exist."
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "message": f"{deleted_count} out of {len(option_ids)} survey options deleted successfully"
        }, status=status.HTTP_200_OK)


# ============ BULK RESTORE ============
class SurveyOptionBulkRestoreView(APIView):
    """
    استعادة مجموعة خيارات استبيان محذوفة
    POST: /api/survey-options/bulk-restore/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request):
        option_ids = request.data.get('ids', [])
        
        if not option_ids:
            return Response({
                "message": "please provide ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(option_ids, list):
            return Response({
                "message": "ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        restored_count = SurveyOptions.objects.filter(
            id__in=option_ids, 
            deleted_at__isnull=False
        ).update(deleted_at=None)
        
        if restored_count == 0:
            return Response({
                "message": "no survey options were restored. they may not be deleted or not exist."
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "message": f"{restored_count} out of {len(option_ids)} survey options restored successfully"
        }, status=status.HTTP_200_OK)


# ============ GET DELETED SURVEY OPTIONS ============
class SurveyOptionDeletedListView(generics.ListAPIView):
    """
    عرض قائمة خيارات الاستبيان المحذوفة
    GET: /api/survey-options/deleted/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = SurveyOptionsDeletedListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['survey']
    search_fields = ['option_text']
    ordering_fields = ['deleted_at', 'created_at']
    ordering = ['-deleted_at']
    pagination_class = CompactPagination
    
    def get_queryset(self):
        return SurveyOptions.objects.filter(deleted_at__isnull=False)


# ============ VOTE ON SURVEY OPTION ============
class SurveyOptionVoteView(APIView):
    """
    التصويت على خيار استبيان
    POST: /api/survey-options/vote/{id}/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def post(self, request, id):
        try:
            option = SurveyOptions.objects.get(
                id=id, 
                deleted_at__isnull=True,
                survey__is_active=True,
                survey__deleted_at__isnull=True
            )
            
            # التحقق من أن الاستبيان لم يغلق
            if option.survey.closes_at and option.survey.closes_at <= timezone.now():
                return Response({
                    "message": "This survey is closed and cannot accept votes"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            option.vote_count += 1
            option.save()
            
            serializer = SurveyOptionsDetailSerializer(option)
            return Response({
                "message": "Vote recorded successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except SurveyOptions.DoesNotExist:
            return Response({
                "message": "Survey option not found or survey is inactive"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ GET OPTIONS BY SURVEY ============
class SurveyOptionsBySurveyView(generics.ListAPIView):
    """
    عرض خيارات استبيان محدد
    GET: /api/survey-options/by-survey/{survey_id}/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = SurveyOptionsListSerializer
    pagination_class = CompactPagination
    
    def get_queryset(self):
        survey_id = self.kwargs.get('survey_id')
        queryset = SurveyOptions.objects.filter(
            survey_id=survey_id,
            deleted_at__isnull=True
        )
        
        # للمستخدمين غير المسجلين، عرض فقط خيارات الاستبيانات النشطة
        if not self.request.user.is_staff:
            queryset = queryset.filter(survey__is_active=True)
        
        return queryset