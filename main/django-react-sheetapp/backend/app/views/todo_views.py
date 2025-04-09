import logging
from django.shortcuts import get_object_or_404
# --- Import IntegrityError ---
from django.db import transaction, models, IntegrityError
from rest_framework import viewsets, generics, status, permissions, views
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound

# Use relative imports within the app
from ..models import Todo, TodoStatus, Page, Row, PagePermission
from ..serializers import (
    TodoListSerializer, TodoDetailSerializer, TodoCreateSerializer,
    TodoStatusSerializer, TodoStatusUpdateSerializer
)
from ..permissions import IsCreatorOrAdminTodo, check_permission, CanViewPage # Use relative import

logger = logging.getLogger(__name__) # Use logger from settings

class TodoViewSet(viewsets.ModelViewSet):
    """
    API endpoint for listing, creating, retrieving, deleting ToDo lists,
    and updating individual item statuses.
    """
    serializer_class = TodoListSerializer # Default serializer for list view
    permission_classes = [permissions.IsAuthenticated] # Base: Must be logged in
    lookup_field = 'pk' # Use primary key (UUID) for detail routes (/api/todos/{pk}/)

    def get_queryset(self):
        """
        Filter ToDo lists based on user access:
        - Admins see all.
        - Authenticated users see ToDos they created OR non-personal ToDos
          linked to source pages they have VIEW access to.
        """
        user = self.request.user

        if not user.is_authenticated:
            return Todo.objects.none()

        if user.is_superuser or user.is_staff:
            logger.debug(f"Admin/Staff user '{user.email}' fetching all ToDos.")
            return Todo.objects.all().select_related('creator', 'source_page')

        logger.debug(f"Filtering ToDos for authenticated user: {user.email}")
        # Get IDs of pages the user can view (using the permission helper)
        # This can be optimized further if performance becomes an issue.
        viewable_page_ids = [
            page.id for page in Page.objects.select_related('owner').iterator()
            if check_permission(user, page, PagePermission.Level.VIEW)
        ]
        # Alternative: Build complex Q object (might be faster for many pages/permissions)
        # user_groups = user.member_of_groups.all()
        # viewable_page_ids = Page.objects.filter(...).values_list('id', flat=True)

        created_by_user_q = models.Q(creator=user)
        viewable_non_personal_q = models.Q(is_personal=False, source_page_id__in=viewable_page_ids)

        return Todo.objects.filter(
            created_by_user_q | viewable_non_personal_q
        ).distinct().select_related('creator', 'source_page').order_by('-created_at')


    def get_serializer_class(self):
        """ Return appropriate serializer based on the request action. """
        if self.action == 'retrieve':
            return TodoDetailSerializer
        elif self.action == 'create':
             return TodoCreateSerializer
        elif self.action == 'update_status': # For the custom action
             return TodoStatusUpdateSerializer
        # Add update/partial_update if allowing direct Todo metadata changes
        # elif self.action in ['update', 'partial_update']:
        #    return SomeTodoUpdateSerializer
        return TodoListSerializer # Default for list

    def get_permissions(self):
        """
        Instantiate and return the list of permissions that this view requires,
        based on the current action.
        """
        base_perms = [permissions.IsAuthenticated]

        if self.action in ['update', 'partial_update', 'destroy', 'update_status']:
            # Requires creator/admin or specific rights for modification/deletion
            # IsCreatorOrAdminTodo checks this based on is_personal and source page view rights
            permission_classes = base_perms + [IsCreatorOrAdminTodo]
        elif self.action == 'retrieve':
             # Viewing also requires specific access rights checked by IsCreatorOrAdminTodo
             permission_classes = base_perms + [IsCreatorOrAdminTodo]
        elif self.action == 'create':
             # Just need to be authenticated, permission to view source page checked in serializer
             permission_classes = base_perms
        else: # list action
             permission_classes = base_perms # Filtering happens in get_queryset

        return [permission() for permission in permission_classes]

    @transaction.atomic # Ensure ToDo and initial statuses are created transactionally
    def perform_create(self, serializer):
        """
        Sets the creator and source_page instance when creating a ToDo,
        and initializes row statuses.
        """
        user = self.request.user
        # source_page instance is validated and attached to context by the serializer
        source_page = serializer.context.get('source_page_instance')

        if not source_page:
             logger.error("Source page instance missing from context during ToDo perform_create.")
             raise ValidationError("Internal error: Source page context missing.")

        logger.info(f"User {user.email} attempting perform_create for ToDo '{serializer.validated_data.get('name')}' from page '{source_page.slug}'")
        try:
            # Pass creator and source_page instance explicitly to serializer.save()
            # The overridden serializer's create method handles validated_data correctly.
            todo = serializer.save(creator=user, source_page=source_page)
            logger.info(f"ToDo '{todo.name}' (ID: {todo.id}) instance created by serializer.")

            # Initialize statuses AFTER the ToDo instance has been successfully created and saved
            todo.initialize_statuses()
            logger.info(f"Initialized statuses for ToDo {todo.id}")

        # --- Catch IntegrityError (now imported) ---
        except IntegrityError as e:
             logger.error(f"Database integrity error creating ToDo for user {user.email} on page {source_page.slug}: {e}", exc_info=True)
             # Provide a user-friendly error message
             raise ValidationError("Failed to create ToDo due to a database conflict. A ToDo with a similar name might already exist for this page.")
        except ValidationError as e:
             # Re-raise validation errors from serializer or explicit raises
             logger.warning(f"Validation error during ToDo creation perform_create: {e.detail}")
             raise e
        except Exception as e:
            # Catch any other unexpected errors during save or status initialization
            logger.error(f"Unexpected error during ToDo perform_create for user {user.email}: {e}", exc_info=True)
            raise ValidationError("An unexpected error occurred while creating the ToDo list.")


    def perform_destroy(self, instance):
        """ Handle ToDo list deletion. Permissions checked by get_permissions. """
        todo_id = instance.id
        todo_name = instance.name
        user_email = self.request.user.email
        try:
            # Deleting the Todo instance will cascade delete related TodoStatus entries
            instance.delete()
            logger.info(f"User {user_email} deleted ToDo '{todo_name}' (ID: {todo_id})")
        except Exception as e:
            logger.error(f"Error deleting ToDo {todo_id} by {user_email}: {e}", exc_info=True)
            # Raise a validation error to ensure DRF sends a proper error response
            raise ValidationError("An error occurred while trying to delete the ToDo list.")


    # Custom action for updating status of a specific row within a ToDo list.
    # detail=True: Action operates on a single instance (identified by pk).
    # methods=['patch']: Responds only to PATCH HTTP method.
    # url_path: Defines the URL segment relative to the detail URL. Captures 'row_id'.
    # permission_classes: Overrides default viewset permissions for this action.
    # serializer_class: Specifies serializer for request data validation & swagger docs.
    @action(detail=True, methods=['patch'], url_path='status/(?P<row_id>[^/.]+)',
            permission_classes=[permissions.IsAuthenticated, IsCreatorOrAdminTodo],
            serializer_class=TodoStatusUpdateSerializer)
    def update_status(self, request, pk=None, row_id=None):
        """
        Update the status for a specific row (identified by row_id) within this
        ToDo list (identified by pk).
        Expects PATCH request with payload: {"status": "NEW_STATUS"}
        URL Example: /api/todos/{todo-uuid}/status/{row-uuid}/
        """
        todo = self.get_object() # Fetches ToDo instance using 'pk', checks object permissions

        try:
            # Find the specific TodoStatus entry for this ToDo and Row.
            # Crucially, ensure the Row actually belongs to the ToDo's source Page.
            status_instance = TodoStatus.objects.select_related('row').get(
                todo=todo,
                row_id=row_id, # Use the captured row_id from the URL
                row__page=todo.source_page # Ensure row is linked to the correct page
            )
        except (TodoStatus.DoesNotExist, ValueError): # ValueError handles invalid UUID format for row_id
             logger.warning(f"TodoStatus update requested for invalid row_id '{row_id}' or non-existent status on ToDo '{pk}'")
             raise NotFound("Status entry not found for this row and ToDo list.")
        except Exception as e:
             # Catch unexpected errors during fetch
             logger.error(f"Error fetching TodoStatus for ToDo {pk}, row {row_id}: {e}", exc_info=True)
             # Return a generic server error response
             return Response({"error": "Internal server error fetching status information."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Validate the incoming request data using the specified serializer
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True) # Raise validation error if data is invalid
        except ValidationError as e:
             logger.warning(f"Invalid status update data for ToDo {pk}, row {row_id}: {e.detail}")
             return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        new_status = serializer.validated_data['status']
        # Only perform DB update if the status is actually changing
        if status_instance.status != new_status:
            try:
                status_instance.status = new_status
                # Update only the 'status' field for efficiency
                status_instance.save(update_fields=['status'])
                logger.info(f"User {request.user.email} updated status for ToDo '{todo.name}', row {status_instance.row.order} (ID: {row_id}) to {new_status}")
                # Return the updated TodoStatus object data on success
                return Response(TodoStatusSerializer(status_instance).data, status=status.HTTP_200_OK)
            except Exception as e:
                 # Catch errors during the save operation
                 logger.error(f"Error saving updated status for ToDo {pk}, row {row_id}: {e}", exc_info=True)
                 return Response({"error": "Failed to save the status update."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
             # If status hasn't changed, just return the current status with 200 OK
             logger.debug(f"Status update requested but no change needed for ToDo {pk}, row {row_id}. Current status: {new_status}")
             return Response(TodoStatusSerializer(status_instance).data, status=status.HTTP_200_OK)
