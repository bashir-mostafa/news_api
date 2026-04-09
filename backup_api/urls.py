# backup_api/urls.py
from django.urls import path
from .views import (
    ListBackupsAPIView,
    CreateBackupAPIView,
    RestoreBackupAPIView,
    ReplaceBackupAPIView,
    DirectUploadAndRestoreAPIView,
    DirectUploadAndReplaceAPIView,  
    DeleteBackupAPIView,
    DownloadBackupAPIView
)

urlpatterns = [
    path('backup/', ListBackupsAPIView.as_view(), name='backup-list'),
    path('backup/create/', CreateBackupAPIView.as_view(), name='backup-create'),
    
    path('backup/restore/', RestoreBackupAPIView.as_view(), name='backup-restore'),
    path('backup/replace/', ReplaceBackupAPIView.as_view(), name='backup-replace'),
    
    path('backup/direct-restore/', DirectUploadAndRestoreAPIView.as_view(), name='backup-direct-restore'),
    path('backup/direct-replace/', DirectUploadAndReplaceAPIView.as_view(), name='backup-direct-replace'),  
    
    path('backup/delete/<str:filename>/', DeleteBackupAPIView.as_view(), name='backup-delete'),
    path('backup/download/<str:filename>/', DownloadBackupAPIView.as_view(), name='backup-download'),
]