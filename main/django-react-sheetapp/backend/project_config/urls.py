"""
Root URL Configuration for the Django project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include # Import include

urlpatterns = [
    # Django Admin site URLs
    path('admin/', admin.site.urls),

    # Include URLs from your application ('app') under the '/api/' prefix
    # All URLs defined in app/urls.py will be accessible via /api/...
    path('api/', include('app.urls')),

    # Add other top-level URL patterns here if needed
    # e.g., path('accounts/', include('django.contrib.auth.urls')), # If using Django's built-in auth views/templates
]