# This file makes the 'views' directory a Python package.
# It allows easier importing of views.
# e.g., from app.views import PageViewSet

# Import view modules to make them accessible via app.views
from . import auth_views
from . import page_views
from . import todo_views
# from . import permission_views # Add later if creating Group/Permission management views

# Optionally define __all__ if you want to control wildcard imports
# __all__ = ['auth_views', 'page_views', 'todo_views']