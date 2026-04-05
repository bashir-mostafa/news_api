# accounts/urls.py
from django.urls import path
from .views import CSRFAPIView, login_view, logout_view, refresh_token_view, user_view

urlpatterns = [
    # ============ المصادقة (Authentication) ============
    # إذا كان عندك CustomTokenObtainPairView و CustomTokenRefreshView و LogoutView
    path('login/', login_view.LoginAPIView.as_view(), name='login'),
    path('token/refresh/', refresh_token_view.RefreshTokenAPIView.as_view(), name='token_refresh'),
    path('logout/', logout_view.LogoutAPIView.as_view(), name='logout'),
    
    # ============ البروفايل الشخصي ============
    path('me/', user_view.UserProfileAPIView.as_view(), name='profile'),
    
    # ============ عمليات المستخدمين الأساسية ============
    # list (GET) and create (POST)
    path('users/', user_view.UserListCreateAPIView.as_view(), name='user-list-create'),
    
    # retrieve (GET), update (PUT/PATCH), delete (DELETE)
    path('users/<int:pk>/', user_view.UserRetrieveUpdateDestroyAPIView.as_view(), name='user-detail'),
    
    # ============ عمليات إضافية ============
    # bulk delete (DELETE)
    path('users/bulk-deleted/', user_view.UserBulkDeleteAPIView.as_view(), name='user-bulk-delete'),
    
    # # activate/deactivate (POST)
    # path('users/<int:user_id>/toggle-status/', user_view.UserActivateDeactivateAPIView.as_view(), name='user-toggle-status'),
    
    # # restore deleted user (POST)
    # path('users/<int:user_id>/restore/', user_view.UserRestoreAPIView.as_view(), name='user-restore'),
]