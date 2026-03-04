# authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework.exceptions import AuthenticationFailed

class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom authentication class that reads JWT from cookies
    """
    
    def authenticate(self, request):
        # محاولة الحصول على التوكن من الكوكي أولاً
        access_token = request.COOKIES.get('access_token')
        
        if not access_token:
            # إذا لم يوجد في الكوكي، جرب الهيدر (كخيار احتياطي)
            header = self.get_header(request)
            if header:
                access_token = self.get_raw_token(header)
            else:
                return None
        
        if access_token is None:
            return None
        
        try:
            # التحقق من صحة التوكن
            validated_token = self.get_validated_token(access_token)
            return self.get_user(validated_token), validated_token
        except InvalidToken:
            raise AuthenticationFailed('التوكن غير صالح أو منتهي الصلاحية')