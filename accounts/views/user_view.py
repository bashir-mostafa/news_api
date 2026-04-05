from rest_framework import serializers 

from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from ..models import CustomUser
from ..serializers import UserSerializer, UserListSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from ..filters import UserFilter
from ..pagination import CompactPagination, KoreanStylePagination, PageNumberPaginationWithRange
from datetime import datetime

# ============ LIST & CREATE ============
class UserListCreateAPIView(generics.ListCreateAPIView):
    queryset = CustomUser.objects.filter(deleted_at__isnull=True)
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = UserFilter.UserFilter
    pagination_class = CompactPagination
    search_fields = ['username', 'email', 'full_name']
    ordering_fields = ['created_at', 'username', 'role']
    ordering = ['-created_at'] 
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        created_at_gte = self.request.query_params.get('createdAt_gte')
        created_at_lte = self.request.query_params.get('createdAt_lte')
        
        if created_at_gte:
            dt = datetime.strptime(created_at_gte, '%Y-%m-%d')
            aware_dt = timezone.make_aware(dt)
            queryset = queryset.filter(created_at__gte=aware_dt)
        
        if created_at_lte:
            dt = datetime.strptime(created_at_lte, '%Y-%m-%d')
            dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            aware_dt = timezone.make_aware(dt)
            queryset = queryset.filter(created_at__lte=aware_dt)
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserListSerializer
        return UserSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            return Response({
                "message": "User created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except serializers.ValidationError as e:
            return Response({
                "message": e.detail
            }, status=status.HTTP_400_BAD_REQUEST)

# ============ RETRIEVE, UPDATE, DELETE ============
class UserRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomUser.objects.filter(deleted_at__isnull=True)
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.is_active = False
        instance.save()
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            
            return Response({
                "message": "User retrieved successfully",
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
            
            return Response({
                "message": "User updated successfully",
                "data": serializer.data
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
            self.perform_destroy(instance)
            
            return Response({
                "message": "User deleted successfully"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ PROFILE ============
class UserProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


# ============ BULK DELETE ============
class UserBulkDeleteAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request):
        user_ids = request.data.get('ids', [])
        
        if not user_ids:
            return Response({
                "message": "Please provide ids"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(user_ids, list):
            return Response({
                "message": "ids must be a list"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if request.user.id in user_ids:
            return Response({
                "message": "You cannot delete yourself"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        deleted_count = CustomUser.objects.filter(
            id__in=user_ids, 
            deleted_at__isnull=True
        ).update(
            deleted_at=timezone.now(),
            updated_by=request.user  
        )
        
        if deleted_count == 0:
            return Response({
                "message": "No users were deleted. They may already be deleted or not exist."
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "message": f"{deleted_count} out of {len(user_ids)} users deleted successfully"
        }, status=status.HTTP_200_OK)  

# ============ DEACTIVATE/ACTIVATE ============
# class UserActivateDeactivateAPIView(APIView):
#     permission_classes = (IsAuthenticated,)

#     def post(self, request, user_id):
#         if request.user.id == user_id:
#             return Response({
#                 "message": "You cannot activate/deactivate yourself"
#             }, status=status.HTTP_400_BAD_REQUEST)
        
#         try:
#             user = CustomUser.objects.get(id=user_id, deleted_at__isnull=True)
#             action = request.data.get('action')
            
#             if not action:
#                 return Response({
#                     "message": "action is required (activate or deactivate)"
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             if action == 'deactivate':
#                 if not user.is_active:
#                     return Response({
#                         "message": "User is already deactivated"
#                     }, status=status.HTTP_400_BAD_REQUEST)
                
#                 user.is_active = False
#                 message = "User deactivated successfully"
                
#             elif action == 'activate':
#                 if user.is_active:
#                     return Response({
#                         "message": "User is already activated"
#                     }, status=status.HTTP_400_BAD_REQUEST)
                
#                 user.is_active = True
#                 message = "User activated successfully"
                
#             else:
#                 return Response({
#                     "message": "Invalid action. Use 'activate' or 'deactivate'"
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             user.updated_by = request.user
#             user.save()
            
#             return Response({
#                 "message": message,
#                 "data": {
#                     "id": user.id,
#                     "username": user.username,
#                     "is_active": user.is_active
#                 }
#             }, status=status.HTTP_200_OK)
            
#         except CustomUser.DoesNotExist:
#             return Response({
#                 "message": "User not found"
#             }, status=status.HTTP_404_NOT_FOUND)

# # ============ RESTORE DELETED ============
# class UserRestoreAPIView(APIView):
#     permission_classes = (IsAuthenticated,)

#     def post(self, request, user_id):
#         try:
#             user = CustomUser.objects.get(id=user_id)
            
#             if user.deleted_at is None:
#                 return Response(
#                     {"error": "User is not deleted"}, 
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
            
#             user.deleted_at = None
#             user.updated_by = request.user
#             user.save()
            
#             return Response(
#                 {"message": "User restored successfully"}, 
#                 status=status.HTTP_200_OK
#             )
            
#         except CustomUser.DoesNotExist:
#             return Response(
#                 {"error": "User not found"}, 
#                 status=status.HTTP_404_NOT_FOUND
#             )