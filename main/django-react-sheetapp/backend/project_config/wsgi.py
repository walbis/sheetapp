"""
WSGI config for project_config project.

It exposes the WSGI callable as a module-level variable named ``application``.
This file is the entry point for WSGI-compatible web servers to serve your project.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Set the default Django settings module for the 'wsgi' application.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_config.settings')

# Get the WSGI application handler.
application = get_wsgi_application()