# accounts/urls.py
from django.urls import path
from .views import login, logout, refresh_token, UserView, CSRFAPIView

urlpatterns = [
    # ============ المصادقة (Authentication) ============
    # إذا كان عندك CustomTokenObtainPairView و CustomTokenRefreshView و LogoutView
    path('login/', login.LoginAPIView.as_view(), name='login'),
    path('token/refresh/', refresh_token.RefreshTokenAPIView.as_view(), name='token_refresh'),
    path('logout/', logout.LogoutAPIView.as_view(), name='logout'),
    
    # ============ البروفايل الشخصي ============
    path('profile/', UserView.UserProfileAPIView.as_view(), name='profile'),
    
    # ============ عمليات المستخدمين الأساسية ============
    # list (GET) and create (POST)
    path('users/', UserView.UserListCreateAPIView.as_view(), name='user-list-create'),
    
    # retrieve (GET), update (PUT/PATCH), delete (DELETE)
    path('users/<int:pk>/', UserView.UserRetrieveUpdateDestroyAPIView.as_view(), name='user-detail'),
    
    # ============ عمليات إضافية ============
    # bulk delete (DELETE)
    path('users/bulk-delete/', UserView.UserBulkDeleteAPIView.as_view(), name='user-bulk-delete'),
    
    # activate/deactivate (POST)
    path('users/<int:user_id>/toggle-status/', UserView.UserActivateDeactivateAPIView.as_view(), name='user-toggle-status'),
    
    # restore deleted user (POST)
    path('users/<int:user_id>/restore/', UserView.UserRestoreAPIView.as_view(), name='user-restore'),
]