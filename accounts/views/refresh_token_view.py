from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import Token
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.jwt import set_token_cookies
from accounts.models import CustomUser 


class RefreshTokenAPIView(TokenRefreshView):
    def post(self, request: Request, *args, **kwargs) -> Response:
        try:
            refresh_token = self.get_refresh_token_from_cookie()
            serializer = self.get_serializer(data={"refresh": refresh_token})
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0]) from e

        access_token = serializer.validated_data.get("access")
        
        from rest_framework_simplejwt.tokens import RefreshToken
        
        try:
            refresh_token_obj = RefreshToken(refresh_token)
            user_id = refresh_token_obj['user_id']
            
            user = CustomUser.objects.get(id=user_id)
            
        except Exception as e:
            raise PermissionDenied(f"User not found: {str(e)}")

        # Set auth cookies
        response = Response({
            "message": "Token refreshed successfully",
            "data": {
                "access_token": access_token,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": getattr(user, 'full_name', ''),
                    "role": getattr(user, 'role', 'user')
                }
            }
        }, status=status.HTTP_200_OK)
        
        set_token_cookies(response, access_token, refresh_token)

        return response

    def get_refresh_token_from_cookie(self) -> str:
        refresh = self.request.COOKIES.get(settings.SIMPLE_JWT.get("AUTH_COOKIE_REFRESH"))
        if not refresh:
            raise PermissionDenied("Refresh token not found")

        return refresh