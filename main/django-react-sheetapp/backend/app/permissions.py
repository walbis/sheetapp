from rest_framework import permissions
from .models import PagePermission, Page, Group, Todo, User # Import User model

import logging
logger = logging.getLogger(__name__) # Use the logger configured in settings.py

# --- Helper Function ---

def check_permission(user, page, required_level):
    """
    Checks if a user has the required permission level (or higher) for a specific page.

    Args:
        user (User): The user object (can be AnonymousUser).
        page (Page): The page instance to check permissions for.
        required_level (PagePermission.Level): The minimum permission level required.

    Returns:
        bool: True if the user has the required permission, False otherwise.
    """
    if not isinstance(page, Page):
        logger.warning(f"check_permission called with non-Page object: {type(page)}")
        return False # Cannot check permission on non-page objects

    # 1. Handle Anonymous User
    if not user or not user.is_authenticated:
        # Anonymous users can only potentially have public VIEW permission
        has_perm = required_level == PagePermission.Level.VIEW and \
               PagePermission.objects.filter(page=page, level=PagePermission.Level.VIEW, target_type=PagePermission.TargetType.PUBLIC).exists()
        # logger.debug(f"Anonymous user check for page '{page.slug}', level {required_level}: {'Allowed' if has_perm else 'Denied'}")
        return has_perm

    # 2. Handle Superuser and Page Owner
    # Ensure user is an instance of your User model if check_permission is called elsewhere
    if isinstance(user, User):
        if user.is_superuser or page.owner == user:
            # logger.debug(f"User '{user.email}' is owner/superuser for page '{page.slug}': Allowed all levels.")
            return True
    else:
         logger.error(f"check_permission called with non-User object for authenticated check: {type(user)}")
         return False # Should not happen in DRF context

    # 3. Determine Allowed Permission Levels
    # Users with higher permission levels implicitly have lower levels.
    allowed_levels = set()
    if required_level == PagePermission.Level.MANAGE:
        allowed_levels.add(PagePermission.Level.MANAGE)
    if required_level == PagePermission.Level.EDIT: # Edit also requires Manage
        allowed_levels.add(PagePermission.Level.EDIT)
        allowed_levels.add(PagePermission.Level.MANAGE)
    if required_level == PagePermission.Level.VIEW: # View requires Edit or Manage too
        allowed_levels.add(PagePermission.Level.VIEW)
        allowed_levels.add(PagePermission.Level.EDIT)
        allowed_levels.add(PagePermission.Level.MANAGE)

    # 4. Check Direct User Permissions
    # Use values_list for efficiency if only existence is needed
    has_user_perm = PagePermission.objects.filter(
        page=page,
        level__in=allowed_levels,
        target_type=PagePermission.TargetType.USER,
        target_user=user
    ).exists()
    if has_user_perm:
        # logger.debug(f"User '{user.email}' has direct perm for page '{page.slug}', allowing level {required_level}: Allowed")
        return True

    # 5. Check Group Permissions
    # Fetch user's group IDs efficiently
    user_group_ids = list(user.member_of_groups.values_list('id', flat=True)) # Get list of group IDs
    if user_group_ids: # Only query if the user belongs to any groups
        has_group_perm = PagePermission.objects.filter(
            page=page,
            level__in=allowed_levels,
            target_type=PagePermission.TargetType.GROUP,
            target_group_id__in=user_group_ids # Query using group IDs
        ).exists()
        if has_group_perm:
            # logger.debug(f"User '{user.email}' has group perm for page '{page.slug}', allowing level {required_level}: Allowed")
            return True

    # 6. Check Public View Permission (only if VIEW level was originally required)
    # This check is for authenticated users who might not have specific user/group perms but the page is public viewable.
    if required_level == PagePermission.Level.VIEW:
        has_public_view = PagePermission.objects.filter(
            page=page,
            level=PagePermission.Level.VIEW,
            target_type=PagePermission.TargetType.PUBLIC
        ).exists()
        if has_public_view:
             # logger.debug(f"Authenticated user '{user.email}' allowed VIEW on page '{page.slug}' via Public permission")
             return True

    # 7. Deny if no permissions found
    # logger.debug(f"User '{user.email}' permission check failed for page '{page.slug}', required level {required_level}: Denied")
    return False


# --- DRF Permission Classes ---

class CanViewPage(permissions.BasePermission):
    """ Allows access only if user has VIEW permission for the page object. """
    message = "You do not have permission to view this page."

    def has_permission(self, request, view):
        # For list views, filtering should happen in get_queryset.
        # For retrieve actions, has_object_permission is the main check.
        return True # Allow request to proceed to object-level check or queryset filtering

    def has_object_permission(self, request, view, obj):
        # obj is expected to be a Page instance in detail views (retrieve)
        if isinstance(obj, Page):
            return check_permission(request.user, obj, PagePermission.Level.VIEW)
        # If used on a view where obj is not a Page, deny access.
        logger.warning(f"CanViewPage used on non-Page object: {type(obj)}")
        return False

class CanEditPage(permissions.BasePermission):
    """ Allows access only if user has EDIT permission for the page object. """
    message = "You do not have permission to edit this page."

    def has_permission(self, request, view):
        # User must be authenticated to attempt editing actions
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # obj is expected to be a Page instance
        if isinstance(obj, Page):
            return check_permission(request.user, obj, PagePermission.Level.EDIT)
        logger.warning(f"CanEditPage used on non-Page object: {type(obj)}")
        return False

class CanManagePagePermissions(permissions.BasePermission):
    """ Allows access only if user has MANAGE permission for the page object. """
    message = "You do not have permission to manage permissions for this page."

    def has_permission(self, request, view):
        # User must be authenticated to attempt permission management
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # obj is expected to be a Page instance
        if isinstance(obj, Page):
            return check_permission(request.user, obj, PagePermission.Level.MANAGE)
        logger.warning(f"CanManagePagePermissions used on non-Page object: {type(obj)}")
        return False

# --- ToDo Specific Permissions ---

class IsCreatorOrAdminTodo(permissions.BasePermission):
    """
    Allows access only to the ToDo creator or admin users.
    For non-personal ToDos, also allows users who can VIEW the source page.
    Used for Retrieve, Update, Delete actions on ToDo objects.
    """
    message = "You do not have permission to access this ToDo list."

    def has_permission(self, request, view):
         # User must be authenticated to access any ToDo details/actions
         return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # obj is expected to be a Todo instance
        if not isinstance(obj, Todo):
            logger.warning(f"IsCreatorOrAdminTodo used on non-Todo object: {type(obj)}")
            return False

        is_creator = obj.creator == request.user
        # Check if user is staff/superuser
        is_admin = request.user and (request.user.is_staff or request.user.is_superuser)

        # Allow creator or admin access immediately
        if is_creator or is_admin:
            # logger.debug(f"ToDo access allowed for {obj.id}: User is creator or admin.")
            return True

        # If not creator/admin, check if it's non-personal AND user can view source page
        if not obj.is_personal:
            # Check if the user has VIEW permission on the source page
            can_view_source = check_permission(request.user, obj.source_page, PagePermission.Level.VIEW)
            # logger.debug(f"ToDo access check for non-personal {obj.id}: Can view source = {can_view_source}")
            return can_view_source

        # If personal and not creator/admin, deny access.
        # logger.debug(f"ToDo access denied for {obj.id}: Not creator/admin and personal, or cannot view source.")
        return False


# --- General Permissions (Example) ---

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Allows access only to the object's owner or admin (staff/superuser) users.
    Assumes the object has an 'owner' attribute linking to a User model.
    """
    message = "Only the owner or an administrator can perform this action."

    def has_permission(self, request, view):
         # Must be authenticated to check ownership/admin status
         return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Check if the object has an 'owner' attribute
        if hasattr(obj, 'owner'):
            is_owner = obj.owner == request.user
            is_admin = request.user and (request.user.is_staff or request.user.is_superuser)
            # logger.debug(f"IsOwnerOrAdmin check for obj {obj}: owner={is_owner}, admin={is_admin}")
            return is_owner or is_admin
        # Log a warning if used on an object without an owner attribute
        logger.warning(f"IsOwnerOrAdmin permission check used on object without 'owner' attribute: {type(obj)}")
        return False # Deny if no owner attribute