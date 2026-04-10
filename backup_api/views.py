# backup_api/views.py
from rest_framework import generics, status
from rest_framework.response import Response
from news_api.permission import IsAdmin
from django.http import FileResponse, Http404
from django.conf import settings
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
import tempfile
from .pagination import KoreanStylePagination, PageNumberPaginationWithRange, CompactPagination
from .serializers import (
    BackupSerializer, 
    RestoreSerializer,
    ReplaceSerializer,  
    BackupFileSerializer
)
from .services import BackupService

# ============ 1. LIST backups ============
class ListBackupsAPIView(APIView):
    """
    GET /api/backups/
    عرض قائمة النسخ الاحتياطية مع Pagination
    """
    permission_classes = [IsAdmin]
    
    def get(self, request, *args, **kwargs):
        try:
            service = BackupService()
            backups = service.list_backups()
            
            page_size = int(request.query_params.get('page_size', 10))
            page = int(request.query_params.get('page', 1))
            
            start = (page - 1) * page_size
            end = start + page_size
            
            paginated_backups = backups[start:end]
            
            serializer = BackupFileSerializer(paginated_backups, many=True)
            
            return Response({
                'page': page,
                'total_pages': (len(backups) + page_size - 1) // page_size,
                'total': len(backups),
                'page_size': page_size,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ 2. CREATE backup ============
class CreateBackupAPIView(APIView):  

    permission_classes = [IsAdmin]
    
    def post(self, request, *args, **kwargs):
        try:
            serializer = BackupSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            service = BackupService()
            result = service.create_backup(
                app_names=serializer.validated_data.get('app_names'),
                compress=serializer.validated_data.get('compress', True),
                exclude=serializer.validated_data.get('exclude'),
                include_media=serializer.validated_data.get('include_media', True)
            )
            
            if result['success']:
                return Response({
                    'message': 'Backup created successfully',
                    'data': {
                        'filename': result['filename'],
                        'size': result['size'],
                        'created_at': result['created_at']
                    }
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'message': 'Backup creation failed',
                    'error': result['error']
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ 3. RESTORE backup (من ملف موجود على السيرفر) ============
class RestoreBackupAPIView(APIView):

    permission_classes = [IsAdmin]
    
    def post(self, request, *args, **kwargs):
        try:
            serializer = RestoreSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            service = BackupService()
            result = service.restore_backup(
                backup_filename=serializer.validated_data['backup_file'],
                mode='restore',
                include_media=serializer.validated_data.get('include_media', True)
            )
            
            if result['success']:
                return Response({
                    'message': result['message'],
                    'mode': 'restore (merge)',
                    'status': 'success'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'message': 'Restore failed',
                    'error': result['error']
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ 4. REPLACE backup (من ملف موجود على السيرفر) ============
class ReplaceBackupAPIView(APIView):

    permission_classes = [IsAdmin]
    
    def post(self, request, *args, **kwargs):
        try:
            serializer = ReplaceSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            confirmation = serializer.validated_data.get('confirmation', False)
            if not confirmation:
                return Response({
                    'message': 'REPLACE operation requires confirmation',
                    'error': 'You must set "confirmation": true to proceed',
                    'warning': 'This will DELETE ALL existing data before restoring!'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            service = BackupService()
            result = service.restore_backup(
                backup_filename=serializer.validated_data['backup_file'],
                mode='replace',
                include_media=serializer.validated_data.get('include_media', True)
            )
            
            if result['success']:
                return Response({
                    'message': result['message'],
                    'mode': 'replace (full replacement)',
                    'status': 'success'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'message': 'Replace failed',
                    'error': result['error']
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ 5. DIRECT RESTORE (رفع ملف واستعادة مع دمج) ============
# backup_api/views.py

class DirectUploadAndRestoreAPIView(APIView):
    permission_classes = [IsAdmin]
    parser_classes = [MultiPartParser]
    
    def post(self, request, *args, **kwargs):
        try:
            if 'backup_file' not in request.FILES:
                return Response({
                    'message': 'No backup file provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            uploaded_file = request.FILES['backup_file']
            include_media = request.data.get('include_media', 'true').lower() == 'true'
            
            service = BackupService()
            result = service.restore_from_stream(
                backup_stream=uploaded_file,  
                mode='restore',
                include_media=include_media
            )
            
            if result['success']:
                return Response({
                    'message': result['message'],
                    'mode': 'direct restore (merge)',
                    'filename': uploaded_file.name,
                    'status': 'success'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'message': 'Direct restore failed',
                    'error': result['error']
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ 6. DIRECT REPLACE (رفع ملف واستبدال كامل) ============
class DirectUploadAndReplaceAPIView(APIView):

    permission_classes = [IsAdmin]
    parser_classes = [MultiPartParser]
    
    def post(self, request, *args, **kwargs):
        try:
            if 'backup_file' not in request.FILES:
                return Response({
                    'message': 'No backup file provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            uploaded_file = request.FILES['backup_file']
            include_media = request.data.get('include_media', 'true').lower() == 'true'
            
            confirmation = request.data.get('confirmation', 'false').lower() == 'true'
            if not confirmation:
                return Response({
                    'message': 'DIRECT REPLACE operation requires confirmation',
                    'error': 'You must set confirmation=true',
                    'warning': '⚠️ This will DELETE ALL existing data permanently!'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            service = BackupService()
            result = service.restore_from_stream(
                backup_stream=uploaded_file,  
                mode='replace',
                include_media=include_media
            )
            
            if result['success']:
                return Response({
                    'message': result['message'],
                    'mode': 'direct replace (full replacement)',
                    'filename': uploaded_file.name,
                    'status': 'success',
                    'warning': 'All previous data has been permanently replaced!'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'message': 'Direct replace failed',
                    'error': result['error']
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ 7. DELETE backup ============
class DeleteBackupAPIView(APIView):
    permission_classes = [IsAdmin]
    
    def delete(self, request, filename, *args, **kwargs):
        try:
            service = BackupService()
            result = service.delete_backup(filename)
            
            if result['success']:
                return Response({
                    'message': result['message']
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'message': 'Delete failed',
                    'error': result['error']
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============ 8. DOWNLOAD backup ============
class DownloadBackupAPIView(APIView):

    permission_classes = [IsAdmin]
    
    def get(self, request, filename, *args, **kwargs):
        try:
            backup_dir = settings.BACKUP_CONFIG['BACKUP_DIR']
            backup_file = backup_dir / filename
            
            if not backup_file.exists():
                return Response({
                    'message': 'Backup file not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            response = FileResponse(
                open(backup_file, 'rb'),
                content_type='application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            return Response({
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)