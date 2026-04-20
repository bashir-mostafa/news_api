from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
from content.serializers import EmailSerializer

class SendEmailView(APIView):
    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            message = serializer.validated_data['message']
            
            try:
                send_mail(
                    subject=f'رسالة جديدة من {email}',
                    message=f'المُرسِل: {email}\n\nالرسالة:\n{message}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=['support@nrls.net'],
                    fail_silently=False,
                )
                return Response(
                    {'success': 'تم إرسال الرسالة بنجاح'},
                    status=status.HTTP_200_OK
                )

            except Exception as e:
                return Response(
                    {'error': f'فشل إرسال الإيميل: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        errors = {}
        for field, messages in serializer.errors.items():
            errors[field] = messages[0]  
        
        return Response(
            {'errors': errors},
            status=status.HTTP_400_BAD_REQUEST
        )