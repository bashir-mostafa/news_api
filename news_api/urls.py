from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('accounts.urls') , name='accounts_api'),
    path('api/', include('content.urls') , name='tags_api'),
]
