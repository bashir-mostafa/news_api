from django.contrib.auth import authenticate
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.jwt import set_token_cookies, delete_token_cookies
from accounts.serializers import LoginSerializer


class LoginAPIView(APIView):
    serializer_class = LoginSerializer
    authentication_classes = ()
    permission_classes = ()

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        
        if not serializer.is_valid():
            errors = serializer.errors
            
            if 'username' and 'password' in errors:
                return Response({
                    "message": "the username and password are required"
                }, status=status.HTTP_400_BAD_REQUEST)
            elif 'password' in errors:
                return Response({
                    "message": "the password is required"
                }, status=status.HTTP_400_BAD_REQUEST)
            elif 'username' in errors:
                return Response({
                    "message": "the username is required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]
        user = authenticate(request, username=username, password=password)

        if not user or user.deleted_at is not None:
            return Response({
                "message": "Invalid username or password"
            }, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = Response({
            "message": "login successfully",
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
        
        response.set_cookie(
            'csrftoken',
            get_token(request),
            max_age=30*24*60*60,  
            path='/',
            httponly=False,
            samesite='Lax',
            secure=False,
        )
        
        
        return response
