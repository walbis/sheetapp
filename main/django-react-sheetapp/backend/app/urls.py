from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import page_views, auth_views, todo_views # Import all relevant view modules

# Create a router instance
# Routers automatically generate URL patterns for ViewSets (list, create, retrieve, update, destroy)
router = DefaultRouter()

# Register ViewSets with the router
router.register(r'pages', page_views.PageViewSet, basename='page') # Base name used for URL reversing
router.register(r'todos', todo_views.TodoViewSet, basename='todo')
# Example: Register Group/Permission management ViewSets later if needed
# router.register(r'groups', permission_views.GroupViewSet, basename='group')

# Define URL patterns
# The router.urls includes all patterns generated for the registered ViewSets.
# Add specific non-ViewSet URLs below.
urlpatterns = [
    # Include router-generated URLs (e.g., /api/pages/, /api/pages/{slug}/, /api/todos/, /api/todos/{pk}/)
    path('', include(router.urls)),

    # --- Authentication Endpoints ---
    path('auth/csrf/', auth_views.CsrfTokenView.as_view(), name='auth-csrf'),
    path('auth/register/', auth_views.RegisterView.as_view(), name='auth-register'),
    path('auth/login/', auth_views.LoginView.as_view(), name='auth-login'),
    path('auth/logout/', auth_views.LogoutView.as_view(), name='auth-logout'),
    path('auth/status/', auth_views.AuthStatusView.as_view(), name='auth-status'),
    # Add password reset URLs etc. here if needed

    # --- Page Specific Action Endpoints ---
    # Retrieve full page data (structure + cells)
    path('pages/<slug:page_slug>/data/', page_views.PageDataView.as_view(), name='page-data'),
    # Save page data (structure + cells)
    path('pages/<slug:page_slug>/save/', page_views.PageSaveView.as_view(), name='page-save'),
    # Update column widths specifically
    path('pages/<slug:page_slug>/columns/width/', page_views.ColumnWidthUpdateView.as_view(), name='column-width-update'),
    # List historical versions of a page
    path('pages/<slug:page_slug>/versions/', page_views.PageVersionListView.as_view(), name='page-versions'),
    # Add endpoints for managing page permissions later
    # path('pages/<slug:page_slug>/permissions/', page_views.PagePermissionView.as_view(), name='page-permissions'),

    # --- ToDo Specific Action Endpoints ---
    # Note: Updating ToDo status is handled by the `@action` within the TodoViewSet,
    # which the router maps automatically to a URL like `/api/todos/{todo_pk}/status/{row_id}/`.
    # No separate URL pattern needed here for that specific action.

    # Add other specific action URLs for ToDos if necessary.
]