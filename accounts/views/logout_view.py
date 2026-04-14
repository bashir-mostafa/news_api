from django.contrib.auth import authenticate
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from news_api.permission import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenBlacklistSerializer

from accounts.jwt import set_token_cookies, delete_token_cookies


class LogoutAPIView(APIView):
    serializer_class = TokenBlacklistSerializer

    def post(self, request):
        refresh_token = self.get_refresh_token_from_cookie()
        
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception as e:
                print(f"Error blacklisting token: {e}")
        
        response = Response({"message": "logout successfully"}, status=status.HTTP_200_OK)
        delete_token_cookies(response)
        
        response.delete_cookie('csrftoken', path='/')
        
        return response

    def get_refresh_token_from_cookie(self):
        return self.request.COOKIES.get('refresh_token')
