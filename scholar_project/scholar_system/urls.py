from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('django-admin/', admin.site.urls),  # Changed from 'admin/' to 'django-admin/'
    path('', include('scholar.urls')),
]
