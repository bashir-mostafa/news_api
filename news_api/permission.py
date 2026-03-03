from rest_framework import permissions
from django.conf import settings

class IsAdmin(permissions.BasePermission):
    """Admin يمكنه كل شيء"""
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role == 'admin')


