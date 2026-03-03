from django.shortcuts import render
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, filters, serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.utils import translation
from news_api.permission import IsAdmin
from .models import CustomUser
from .serializers import CustomUserSerializer, CustomTokenObtainPairSerializer

# ===================================================================
# TOKEN AUTHENTICATION
# ===================================================================

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        # تفعيل اللغة المطلوبة من query param ?lang=
        lang = request.GET.get("lang", "ar")
        translation.activate(lang)

        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as exc:
            errors = []

            # إذا كان detail قاموس (مثل ValidationError من serializer)
            if hasattr(exc, 'detail'):
                detail = exc.detail
                if isinstance(detail, dict):
                    for field, messages in detail.items():
                        for msg in messages:
                            errors.append(f"{field}: {_(str(msg))}")
                elif isinstance(detail, list):
                    for msg in detail:
                        errors.append(_(str(msg)))
                else:
                    errors.append(_(str(detail)))
            else:
                errors.append(_(str(exc)))

            return Response(
                {"detail": " | ".join(errors)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # إذا كان كل شيء صحيح
        return Response(
            {
                "detail": _("تم تسجيل الدخول بنجاح")
                 ,**serializer.validated_data
            },
            status=status.HTTP_200_OK
        )


# ===================================================================
# PAGINATION
# ===================================================================
class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100 


# ===================================================================
# PROFILE VIEW
# ===================================================================
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data)


# ===================================================================
# LIST & CREATE USERS
# ===================================================================
class CustomUserListView(generics.ListCreateAPIView):
    permission_classes = [IsAdmin]
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ["id", "username", "first_name", "phone_number", "role", "is_active"]       
    filterset_fields = ["id", "username", "first_name", "phone_number", "role", "is_active"]
    ordering_fields = [ "first_name"]
    ordering = ["created_at"] 

    def create(self, request, *args, **kwargs):
        lang = request.GET.get("lang", "ar")
        translation.activate(lang)

        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as exc:
            all_errors = []
            for field, messages in exc.detail.items():
                for msg in messages:
                    all_errors.append(f"{field}: {_(str(msg))}")
            return Response(
                {"detail": " | ".join(all_errors)},
                status=status.HTTP_400_BAD_REQUEST
            )

        self.perform_create(serializer)
        return Response(
            {
                "detail": _("تم إنشاء المستخدم بنجاح"),
                "results": serializer.data
            },
            status=status.HTTP_201_CREATED
        )


# ===================================================================
# RETRIEVE, UPDATE & DELETE USER
# ===================================================================
class CustomUserRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdmin]
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    lookup_field = "id"

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            instance=self.get_object(),
            data=request.data,
            partial=True
        )
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as exc:
            all_errors = []
            for field, messages in exc.detail.items():
                for msg in messages:
                    all_errors.append(f"{field}: {_(str(msg))}")
            return Response(
                {"detail": " | ".join(all_errors)},
                status=status.HTTP_400_BAD_REQUEST
            )

        self.perform_update(serializer)
        return Response(
            {
                "detail": _("تم تحديث المستخدم بنجاح"),
                "results": serializer.data
            },
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"detail": _("تم حذف المستخدم بنجاح")},
            status=status.HTTP_200_OK
        )


# ===================================================================
# BULK DELETE USERS
# ===================================================================
class CustomUserBulkDeleteView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, *args, **kwargs):
        ids = request.data.get("ids") if isinstance(request.data, dict) else request.data
        if not isinstance(ids, list) or not ids:
            return Response(
                {"detail": _("يرجى تقديم قائمة غير فارغة من المعرفات.")},
                status=status.HTTP_400_BAD_REQUEST
            )

        qs = CustomUser.objects.filter(id__in=ids)
        if not qs.exists():
            return Response(
                {"detail": _("لم يتم العثور على مستخدمين مطابقين.")},
                status=status.HTTP_404_NOT_FOUND
            )

        count_before = qs.count()
        with transaction.atomic():
            qs.delete()

        return Response(
            {"detail": _("{count} مستخدم تم حذفه بنجاح.").format(count=count_before)},
            status=status.HTTP_200_OK
        )
