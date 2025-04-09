"""
ASGI config for project_config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# Set the default Django settings module for the 'asgi' application.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_config.settings')

# Get the ASGI application handler.
application = get_asgi_application()