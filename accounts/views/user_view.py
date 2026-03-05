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

# ============ LIST & CREATE ============
class UserListCreateAPIView(generics.ListCreateAPIView):
    queryset = CustomUser.objects.all()
    
    permission_classes = (IsAuthenticated, IsAdminUser)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = UserFilter.UserFilter
    pagination_class = CompactPagination
    search_fields = ['username', 'email', 'full_name']
    ordering_fields = ['created_at', 'username', 'role']
    ordering = ['-created_at'] 
    
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
        instance.save()


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
        user_ids = request.data.get('user_ids', [])
        if not user_ids:
            return Response(
                {"error": "Please provide user_ids"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.user.id in user_ids:
            return Response(
                {"error": "You cannot delete yourself"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        # soft delete للمستخدمين
        CustomUser.objects.filter(id__in=user_ids, deleted_at__isnull=True).update(
            deleted_at=timezone.now()
        )
        
        return Response(
            {"message": f"{len(user_ids)} users deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )


# ============ DEACTIVATE/ACTIVATE ============
class UserActivateDeactivateAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, user_id):
        try:
            user = CustomUser.objects.get(id=user_id, deleted_at__isnull=True)
            action = request.data.get('action')
            
            if action == 'deactivate':
                user.is_active = False
                message = "User deactivated successfully"
            elif action == 'activate':
                user.is_active = True
                message = "User activated successfully"
            else:
                return Response(
                    {"error": "Invalid action. Use 'activate' or 'deactivate'"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.updated_by = request.user
            user.save()
            
            return Response({"message": message}, status=status.HTTP_200_OK)
            
        except CustomUser.DoesNotExist:
            return Response(
                {"error": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )


# ============ RESTORE DELETED ============
class UserRestoreAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, user_id):
        try:
            user = CustomUser.objects.get(id=user_id)
            
            if user.deleted_at is None:
                return Response(
                    {"error": "User is not deleted"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.deleted_at = None
            user.updated_by = request.user
            user.save()
            
            return Response(
                {"message": "User restored successfully"}, 
                status=status.HTTP_200_OK
            )
            
        except CustomUser.DoesNotExist:
            return Response(
                {"error": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )