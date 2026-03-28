# content/views/surveys_views.py
from rest_framework import generics, status, filters, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from content.pagination import CompactPagination
from content.models import Surveys
from content.serializers import (
    SurveysSerializer,
    SurveysCreateUpdateSerializer,
    SurveysDetailSerializer,
    SurveysListSerializer,
    SurveysDeletedListSerializer
)

# ============ LIST & CREATE ============
class SurveyListCreateView(generics.ListCreateAPIView):
    """
    عرض قائمة الاستبيانات وإنشاء استبيان جديد
    GET: /api/surveys/
    POST: /api/surveys/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['id', 'post', 'is_active']
    pagination_class = CompactPagination
    search_fields = ['question']
    ordering_fields = ['created_at', 'closes_at', 'question']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Surveys.objects.filter(deleted_at__isnull=True)
        
        # تصفية حسب المقال
        post_id = self.request.query_params.get('post')
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        
        # تصفية حسب النشاط
        is_active = self.request.query_params.get('is_active')
        if is_active:
            queryset = queryset.filter(is_active=is_active)
        
        # للمستخدمين غير المسجلين، عرض الاستبيانات النشطة فقط
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SurveysListSerializer
        return SurveysCreateUpdateSerializer
    
    def perform_create(self, serializer):
        serializer.save()
    
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            survey = Surveys.objects.get(id=serializer.instance.id)
            detail_serializer = SurveysDetailSerializer(survey)
            
            return Response({
                "message": "survey created successfully",
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
                "message": "get all surveys successfully",
                "count": queryset.count(),
                "data": serializer.data
            })
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ RETRIEVE, UPDATE, DELETE ============
class SurveyRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """
    عرض وتحديث وحذف استبيان محدد
    GET: /api/surveys/{id}/
    PUT: /api/surveys/{id}/
    PATCH: /api/surveys/{id}/
    DELETE: /api/surveys/{id}/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'id'
    
    def get_queryset(self):
        queryset = Surveys.objects.filter(deleted_at__isnull=True)
        
        # للمستخدمين غير المسجلين، عرض الاستبيانات النشطة فقط
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return SurveysCreateUpdateSerializer
        return SurveysDetailSerializer
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            
            return Response({
                "message": "get survey details successfully",
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
            detail_serializer = SurveysDetailSerializer(updated_instance)
            
            return Response({
                "message": "survey updated successfully",
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
                "message": "survey deleted successfully"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ HARD DELETE ============
class SurveyHardDeleteView(generics.DestroyAPIView):
    """
    حذف نهائي لاستبيان (للمشرفين فقط)
    DELETE: /api/surveys/hard-delete/{id}/
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'id'
    queryset = Surveys.objects.all()
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            survey_id = instance.id
            instance.delete()
            
            return Response({
                "message": f"survey '{survey_id}' deleted permanently successfully"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class SurveyBulkHardDeleteView(APIView):
    """
    حذف نهائي لمجموعة استبيانات (للمشرفين فقط)
    DELETE: /api/surveys/bulk-hard-delete/
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request):
        survey_ids = request.data.get('ids', [])
        
        if not survey_ids:
            return Response({
                "message": "please provide ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(survey_ids, list):
            return Response({
                "message": "ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        surveys = Surveys.objects.filter(id__in=survey_ids)
        found_ids = list(surveys.values_list('id', flat=True))
        
        if not found_ids:
            return Response({
                "message": "no surveys found with the provided ids"
            }, status=status.HTTP_404_NOT_FOUND)
        
        deleted_count = len(found_ids)
        surveys.delete()
        
        return Response({
            "message": f"{deleted_count} out of {len(survey_ids)} surveys deleted permanently successfully",
            "deleted_ids": found_ids
        }, status=status.HTTP_200_OK)


# ============ RESTORE DELETED ============
class SurveyRestoreView(APIView):
    """
    استعادة استبيان محذوف
    POST: /api/surveys/restore/{id}/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, id):
        try:
            survey = Surveys.objects.get(id=id, deleted_at__isnull=False)
            survey.deleted_at = None
            survey.save()
            
            serializer = SurveysDetailSerializer(survey)
            return Response({
                "message": "survey restored successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Surveys.DoesNotExist:
            return Response({
                "message": "survey not found or not deleted"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ BULK DELETE ============
class SurveyBulkDeleteView(APIView):
    """
    حذف ناعم لمجموعة استبيانات
    DELETE: /api/surveys/bulk-delete/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def delete(self, request):
        survey_ids = request.data.get('ids', [])
        
        if not survey_ids:
            return Response({
                "message": "please provide ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(survey_ids, list):
            return Response({
                "message": "ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        deleted_count = Surveys.objects.filter(
            id__in=survey_ids, 
            deleted_at__isnull=True
        ).update(deleted_at=timezone.now())
        
        if deleted_count == 0:
            return Response({
                "message": "no surveys were deleted. they may already be deleted or not exist."
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "message": f"{deleted_count} out of {len(survey_ids)} surveys deleted successfully"
        }, status=status.HTTP_200_OK)


# ============ BULK RESTORE ============
class SurveyBulkRestoreView(APIView):
    """
    استعادة مجموعة استبيانات محذوفة
    POST: /api/surveys/bulk-restore/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request):
        survey_ids = request.data.get('ids', [])
        
        if not survey_ids:
            return Response({
                "message": "please provide ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(survey_ids, list):
            return Response({
                "message": "ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        restored_count = Surveys.objects.filter(
            id__in=survey_ids, 
            deleted_at__isnull=False
        ).update(deleted_at=None)
        
        if restored_count == 0:
            return Response({
                "message": "no surveys were restored. they may not be deleted or not exist."
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "message": f"{restored_count} out of {len(survey_ids)} surveys restored successfully"
        }, status=status.HTTP_200_OK)


# ============ GET DELETED SURVEYS ============
class SurveyDeletedListView(generics.ListAPIView):
    """
    عرض قائمة الاستبيانات المحذوفة
    GET: /api/surveys/deleted/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = SurveysDeletedListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['post', 'is_active']
    search_fields = ['question']
    ordering_fields = ['deleted_at', 'created_at']
    ordering = ['-deleted_at']
    pagination_class = CompactPagination
    
    def get_queryset(self):
        return Surveys.objects.filter(deleted_at__isnull=False)


# ============ ACTIVATE / DEACTIVATE SURVEY ============
class SurveyActivateView(APIView):
    """
    تفعيل استبيان
    POST: /api/surveys/activate/{id}/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def post(self, request, id):
        try:
            survey = Surveys.objects.get(id=id, deleted_at__isnull=True)
            survey.is_active = True
            survey.save()
            
            serializer = SurveysDetailSerializer(survey)
            return Response({
                "message": "survey activated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Surveys.DoesNotExist:
            return Response({
                "message": "survey not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class SurveyDeactivateView(APIView):

    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def post(self, request, id):
        try:
            survey = Surveys.objects.get(id=id, deleted_at__isnull=True)
            survey.is_active = False
            survey.save()
            
            serializer = SurveysDetailSerializer(survey)
            return Response({
                "message": "survey deactivated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Surveys.DoesNotExist:
            return Response({
                "message": "survey not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ GET SURVEYS BY POST ============
class SurveysByPostView(generics.ListAPIView):
    """
    عرض استبيانات مقال محدد
    GET: /api/surveys/by-post/{post_id}/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = SurveysListSerializer
    pagination_class = CompactPagination
    
    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        queryset = Surveys.objects.filter(
            post_id=post_id,
            deleted_at__isnull=True
        )
        
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        
        return queryset