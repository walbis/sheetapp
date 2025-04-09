import logging
from django.shortcuts import get_object_or_404
from django.db import transaction, IntegrityError, models
from django.db.models import Prefetch
from django.http import Http404 # Import Http404 for explicit raising if needed
from rest_framework import viewsets, generics, status, permissions, views
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound
# Use relative imports within the app
from ..models import Page, Column, Row, Cell, Version, PagePermission, User, Group
from ..serializers import (
    PageListSerializer, PageDetailSerializer, PageDataSerializer, VersionSerializer, UserSerializer, UserBasicSerializer,
    ColumnSerializer # Import component serializers if needed
)
from ..permissions import CanViewPage, CanEditPage, CanManagePagePermissions, check_permission

logger = logging.getLogger(__name__) # Use logger configured in settings.py

class PageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling Pages.
    Provides list, create, retrieve, update (metadata), partial_update (metadata), destroy actions.
    Permissions are checked based on the action.
    """
    # Default serializer class used for retrieve, update, partial_update, create
    serializer_class = PageDetailSerializer
    # Field used for looking up individual Page instances (e.g., /api/pages/{slug}/)
    lookup_field = 'slug'

    def get_queryset(self):
        """
        Dynamically filters the queryset based on the requesting user's permissions.
        Ensures users only see pages they are allowed to view in the list endpoint.
        """
        user = self.request.user

        # Case 1: Anonymous User - Only show publicly viewable pages
        if not user.is_authenticated:
            logger.debug("Filtering pages for anonymous user (public VIEW only)")
            # Query for pages that have a PUBLIC VIEW permission entry
            qs = Page.objects.filter(
                permissions__target_type=PagePermission.TargetType.PUBLIC,
                permissions__level=PagePermission.Level.VIEW
            ).distinct() # Use distinct to avoid duplicates if multiple permissions match

        # Case 2: Superuser - Show all pages
        elif user.is_superuser:
            logger.debug(f"Superuser '{user.email}' requested pages list, returning all.")
            qs = Page.objects.all()

        # Case 3: Authenticated User - Combine accessible pages
        else:
            logger.debug(f"Filtering pages for authenticated user: {user.email}")
            # Get the groups the user is a member of
            user_groups = user.member_of_groups.all() # Efficiently gets related groups

            # Build Q objects for combining different access criteria with OR logic
            owned_q = models.Q(owner=user)
            # Check for VIEW level or higher (EDIT/MANAGE imply VIEW) for user/group permissions
            view_levels = [PagePermission.Level.VIEW, PagePermission.Level.EDIT, PagePermission.Level.MANAGE]
            user_perm_q = models.Q(
                permissions__target_type=PagePermission.TargetType.USER,
                permissions__target_user=user,
                permissions__level__in=view_levels
            )
            group_perm_q = models.Q(
                permissions__target_type=PagePermission.TargetType.GROUP,
                permissions__target_group__in=user_groups,
                permissions__level__in=view_levels
            )
            public_perm_q = models.Q(
                permissions__target_type=PagePermission.TargetType.PUBLIC,
                permissions__level=PagePermission.Level.VIEW
            )

            # Combine all conditions using OR (|) and fetch distinct pages
            qs = Page.objects.filter(
                owned_q | user_perm_q | group_perm_q | public_perm_q
            ).distinct()

        # Optimize database query by prefetching the owner details
        # Order results by last updated time
        return qs.select_related('owner').order_by('-updated_at')

    def get_serializer_class(self):
        """ Return the appropriate serializer class depending on the request action. """
        if self.action == 'list':
            # Use the summary serializer for the list view
            return PageListSerializer
        # For retrieve, create, update, partial_update use the detail serializer
        # which handles the 'name' field but not the full cell data.
        return PageDetailSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires,
        depending on the action being performed.
        """
        # Default permissions allow safe methods (GET, HEAD, OPTIONS) if authenticated or read-only
        permission_classes = [permissions.IsAuthenticatedOrReadOnly]

        if self.action in ['update', 'partial_update']:
            # Updating page metadata requires EDIT permission on the specific page object
            permission_classes = [permissions.IsAuthenticated, CanEditPage]
        elif self.action == 'destroy':
             # Deleting a page requires EDIT permission (or potentially a stricter custom permission)
             permission_classes = [permissions.IsAuthenticated, CanEditPage] # Refine if needed
        elif self.action == 'retrieve':
            # Viewing a specific page detail requires VIEW permission
            permission_classes = [CanViewPage] # Allow anonymous if public view exists
        elif self.action == 'create':
            # Creating a new page requires the user to be authenticated
            permission_classes = [permissions.IsAuthenticated]
        # For 'list' action, IsAuthenticatedOrReadOnly allows access,
        # but the actual filtering happens in get_queryset.

        # Return instances of the permission classes
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """
        Custom logic executed after validation when creating a new Page instance.
        Sets the owner, creates default structure, and grants owner permissions.
        """
        user = self.request.user
        page_name = serializer.validated_data.get('name', 'Untitled Page')
        logger.info(f"User '{user.email}' attempting to create page: '{page_name}'")
        try:
            # Use an atomic transaction to ensure all related actions succeed or fail together
            with transaction.atomic():
                # Save the page instance, automatically setting the owner
                page = serializer.save(owner=user)
                logger.info(f"Page '{page.name}' (slug: {page.slug}) created successfully by {user.email}")

                # Set up default columns (e.g., "Column A", "Column B")
                page.setup_default_structure()
                logger.debug(f"Default structure set up for page '{page.slug}'")

                # Grant the creating user full permissions (VIEW, EDIT, MANAGE) on the new page
                permissions_to_grant = [
                    PagePermission(page=page, level=level, target_type=PagePermission.TargetType.USER, target_user=user, granted_by=user)
                    for level in [PagePermission.Level.VIEW, PagePermission.Level.EDIT, PagePermission.Level.MANAGE]
                ]
                PagePermission.objects.bulk_create(permissions_to_grant)
                logger.info(f"Default owner permissions granted for page '{page.slug}' to user '{user.email}'")

        except IntegrityError as e:
            # Handle potential database constraint violations (e.g., slug collision if retry logic fails)
            logger.error(f"Integrity error creating page '{page_name}' for {user.email}: {e}", exc_info=True)
            raise ValidationError("Failed to create page due to a database conflict. The name might already be in use or lead to a duplicate URL.")
        except Exception as e:
             # Catch any other unexpected errors during the creation process
             logger.error(f"Unexpected error creating page for {user.email}: {e}", exc_info=True)
             raise ValidationError("An unexpected error occurred while creating the page.")

    def perform_update(self, serializer):
        """ Handle updates to Page metadata (e.g., changing the 'name'). """
        # Permissions (CanEditPage) are checked by get_permissions() before this method is called
        instance = serializer.instance
        original_name = instance.name
        # Save the updated instance data provided by the serializer
        updated_instance = serializer.save()
        # Log the update action
        logger.info(f"User '{self.request.user.email}' updated page metadata for '{original_name}' -> '{updated_instance.name}' (slug: {instance.slug})")
        # Note: Slug is typically read-only and not updated here.

    def perform_destroy(self, instance):
        """ Handle the deletion of a Page instance. """
        # Permissions (CanEditPage or stricter) checked by get_permissions()
        page_slug = instance.slug
        page_name = instance.name
        user_email = self.request.user.email
        logger.warning(f"User '{user_email}' attempting to delete page '{page_name}' (slug: {page_slug})")
        try:
            # Use atomic transaction if deletion involves complex cascading or related actions
            with transaction.atomic():
                instance.delete() # Perform the deletion
            logger.info(f"Page '{page_name}' (slug: {page_slug}) deleted successfully by '{user_email}'.")
        except Exception as e:
            # Log errors during deletion
            logger.error(f"Error deleting page '{page_slug}' by '{user_email}': {e}", exc_info=True)
            # Raise an error to signal failure
            raise ValidationError("An error occurred while trying to delete the page.")


class PageDataView(generics.RetrieveAPIView):
    """
    API endpoint specifically for retrieving the *full* data required to render a page's table,
    including columns, rows, and all cell values in the correct order.
    """
    serializer_class = PageDataSerializer # Uses the serializer designed for the full data structure
    permission_classes = [CanViewPage]     # Requires VIEW permission on the page object
    lookup_field = 'slug'                  # Use slug from URL to find the Page
    lookup_url_kwarg = 'page_slug'         # The name of the URL keyword argument

    def get_queryset(self):
        """ Optimize the database query by prefetching related objects needed for serialization. """
        # Fetch the Page along with its related owner, columns (ordered), rows (ordered),
        # and within each row, prefetch its cells along with the cell's related column (ordered).
        return Page.objects.all().select_related('owner').prefetch_related(
            Prefetch('columns', queryset=Column.objects.order_by('order')),
            Prefetch('rows', queryset=Row.objects.order_by('order').prefetch_related(
                Prefetch('cells', queryset=Cell.objects.select_related('column').order_by('column__order'))
            ))
        )

    def retrieve(self, request, *args, **kwargs):
        """ Retrieve the Page object and serialize its data into the required format. """
        try:
            # get_object() handles lookup, 404, and permission checks via permission_classes
            page = self.get_object()
        except Http404:
             logger.warning(f"Page data requested but not found: slug={kwargs.get('page_slug')}")
             raise NotFound("Page not found.") # Use DRF's NotFound exception

        user_email = request.user.email if request.user.is_authenticated else "Anonymous"
        logger.debug(f"User '{user_email}' retrieving data for page: '{page.slug}'")

        # 1. Serialize Column Data
        # Use ColumnSerializer defined earlier, getting data from prefetched ordered columns
        columns_data = ColumnSerializer(page.columns.all(), many=True).data

        # 2. Serialize Row and Cell Data
        rows_data = []
        # Create a map from column ID (string) to its 0-based index for quick lookup
        column_id_to_index = {col['id']: i for i, col in enumerate(columns_data)}
        num_columns = len(columns_data)

        # Iterate through prefetched, ordered rows
        for row in page.rows.all():
            # Initialize cell values list with empty strings, matching column count
            ordered_cell_values = [''] * num_columns
            # Iterate through the row's prefetched, ordered cells
            for cell in row.cells.all():
                col_id_str = str(cell.column.id) # Get column UUID as string
                if col_id_str in column_id_to_index:
                    index = column_id_to_index[col_id_str] # Find the correct index for this cell's column
                    ordered_cell_values[index] = cell.value # Place value at the correct index
                else:
                    # Log inconsistency if a cell's column ID isn't found in the page's columns
                     logger.warning(f"Cell (ID:{cell.id}) found for row {row.id} linked to unknown/deleted column {col_id_str} on page {page.slug}")

            # Append the row data (ID, order, ordered cells) to the results
            rows_data.append({
                'id': str(row.id), # Row UUID as string
                'order': row.order,
                'cells': ordered_cell_values
            })

        # 3. Prepare final dictionary matching PageDataSerializer structure
        output_data = {
            'id': str(page.id),
            'name': page.name,
            'slug': page.slug,
            'owner': UserBasicSerializer(page.owner).data, # Include basic owner info
            'columns': columns_data,
            'rows': rows_data,
        }
        # Use the serializer (though we manually constructed the data, this ensures consistency)
        serializer = self.get_serializer(output_data)
        return Response(serializer.data)


class PageSaveView(views.APIView):
    """
    API endpoint to save changes to a page's structure (columns, rows) and cell data.
    This view handles the complex logic of applying differences between the existing
    state and the submitted payload (add, delete, update, reorder).
    It creates a new Version snapshot upon successful save.
    Uses pessimistic locking on the Page row to prevent concurrent save conflicts.
    """
    permission_classes = [permissions.IsAuthenticated, CanEditPage] # Requires EDIT permission

    @transaction.atomic # Ensure all database operations within the save succeed or fail together
    def post(self, request, page_slug):
        """ Handles POST request containing the full page state to save. """
        logger.info(f"User '{request.user.email}' attempting to save page '{page_slug}'")
        try:
            # Fetch the Page instance and lock the row for the duration of the transaction
            # This prevents other transactions from modifying this specific page row concurrently.
            page = Page.objects.select_for_update().get(slug=page_slug)
            logger.debug(f"Pessimistic lock acquired for page '{page_slug}'")
        except Page.DoesNotExist:
            raise NotFound("Page not found.")
        except Exception as e:
             # Catch other potential errors during locking/fetching
             logger.error(f"Error fetching/locking page '{page_slug}' for save: {e}", exc_info=True)
             return Response({"error": "Failed to acquire lock for saving the page."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Check object-level edit permission after fetching the page
        self.check_object_permissions(request, page)

        # Validate the incoming payload structure using PageDataSerializer
        serializer = PageDataSerializer(data=request.data)
        if not serializer.is_valid():
             logger.warning(f"Page save validation failed for '{page_slug}': {serializer.errors}")
             # Return validation errors to the client
             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Get validated data from the serializer
        validated_data = serializer.validated_data
        columns_payload = validated_data.get('columns', [])
        rows_payload = validated_data.get('rows', [])
        commit_message = validated_data.get('commit_message', 'Page updated via API') # Default commit message

        try:
            # --- 1. Process Columns ---
            # Compare existing columns with payload to determine changes

            # Map existing columns by their UUID string for quick lookup
            existing_cols = {str(c.id): c for c in page.columns.all()}
            # Set of column UUID strings present in the payload
            payload_col_ids = {str(c['id']) for c in columns_payload if c.get('id')}
            # Set of column UUID strings to be deleted (exist in DB but not in payload)
            cols_to_delete_ids = set(existing_cols.keys()) - payload_col_ids

            # Delete columns that are no longer in the payload
            if cols_to_delete_ids:
                deleted_count, _ = Column.objects.filter(page=page, id__in=cols_to_delete_ids).delete()
                logger.info(f"Deleted {deleted_count} columns for page '{page_slug}'.")
                # Refresh existing_cols map after deletion for accurate processing below
                existing_cols = {str(c.id): c for c in page.columns.all()}

            # Lists to hold objects for bulk operations
            cols_to_update = []
            cols_to_create = []
            # Keep track of processed columns from payload to ensure validity
            processed_col_ids = set()

            # Iterate through payload columns IN ORDER to handle updates and creations
            for i, col_data in enumerate(columns_payload):
                col_id_str = str(col_data['id']) if col_data.get('id') else None
                target_order = i + 1 # Order is determined by position in payload array

                if col_id_str and col_id_str in existing_cols:
                    # --- Update Existing Column ---
                    col_instance = existing_cols[col_id_str]
                    processed_col_ids.add(col_id_str) # Mark as processed
                    # Check if any field needs updating
                    if (col_instance.name != col_data['name'] or
                        col_instance.order != target_order or
                        col_instance.width != col_data.get('width', 150)): # Use default width if not provided
                        col_instance.name = col_data['name']
                        col_instance.order = target_order
                        col_instance.width = col_data.get('width', 150)
                        cols_to_update.append(col_instance) # Add to bulk update list
                elif not col_id_str:
                    # --- Prepare New Column for Creation ---
                    cols_to_create.append(
                        Column(
                            page=page,
                            name=col_data['name'],
                            order=target_order,
                            width=col_data.get('width', 150)
                        )
                    )
                else:
                    # Error case: Payload contains an ID not found among existing columns
                    logger.error(f"Consistency Error: Column ID '{col_id_str}' in payload not found for page '{page.slug}' after deletions.")
                    raise ValidationError(f"Invalid payload: Column ID '{col_id_str}' does not exist for this page.")

            # Perform bulk database operations for columns
            if cols_to_update:
                Column.objects.bulk_update(cols_to_update, ['name', 'order', 'width'])
                logger.debug(f"Bulk updated {len(cols_to_update)} columns for page '{page.slug}'.")
            if cols_to_create:
                # Bulk create returns the list of created instances (with IDs)
                created_cols = Column.objects.bulk_create(cols_to_create)
                logger.debug(f"Bulk created {len(created_cols)} columns for page '{page.slug}'.")

            # --- Re-fetch columns in their FINAL correct order for cell processing ---
            final_ordered_columns = list(page.columns.order_by('order'))
            # Create maps for easy lookup by ID and order
            final_col_id_map = {str(c.id): c for c in final_ordered_columns}
            final_col_order_map = {c.order: c for c in final_ordered_columns} # Maps order (1, 2, ...) to Column instance

            # --- 2. Process Rows ---
            # Similar logic as for columns: find rows to delete, update, create

            existing_rows = {str(r.id): r for r in page.rows.all()}
            payload_row_ids = {str(r['id']) for r in rows_payload if r.get('id')}
            rows_to_delete_ids = set(existing_rows.keys()) - payload_row_ids

            if rows_to_delete_ids:
                deleted_count, _ = Row.objects.filter(page=page, id__in=rows_to_delete_ids).delete()
                logger.info(f"Deleted {deleted_count} rows for page '{page.slug}'.")
                existing_rows = {str(r.id): r for r in page.rows.all()} # Refresh map

            rows_to_update = []
            rows_to_create = []
            # Map to hold final row instances (keyed by their final order) for cell processing
            final_ordered_rows_map = {} # Maps order (1, 2, ...) to Row instance
            processed_row_ids = set()

            for i, row_data in enumerate(rows_payload):
                row_id_str = str(row_data['id']) if row_data.get('id') else None
                target_order = i + 1 # Order determined by payload position

                row_instance = None
                if row_id_str and row_id_str in existing_rows:
                    # --- Update Existing Row Order ---
                    row_instance = existing_rows[row_id_str]
                    processed_row_ids.add(row_id_str) # Mark as processed
                    if row_instance.order != target_order:
                        row_instance.order = target_order
                        rows_to_update.append(row_instance)
                elif not row_id_str:
                    # --- Prepare New Row for Creation ---
                    # Create instance but don't save yet (bulk_create later)
                    row_instance = Row(page=page, order=target_order)
                    rows_to_create.append(row_instance)
                else:
                    logger.error(f"Consistency Error: Row ID '{row_id_str}' in payload not found for page '{page.slug}' after deletions.")
                    raise ValidationError(f"Invalid payload: Row ID '{row_id_str}' does not exist for this page.")

                if row_instance: # Track the instance (saved or unsaved) by its intended final order
                     final_ordered_rows_map[target_order] = row_instance

            # Perform bulk operations for rows
            if rows_to_update:
                Row.objects.bulk_update(rows_to_update, ['order'])
                logger.debug(f"Bulk updated {len(rows_to_update)} row orders for page '{page.slug}'.")
            if rows_to_create:
                # Create new rows and get back instances with generated IDs
                created_rows = Row.objects.bulk_create(rows_to_create)
                logger.debug(f"Bulk created {len(created_rows)} rows for page '{page.slug}'.")
                # Update the map with the newly created instances (using their order)
                for r in created_rows:
                    final_ordered_rows_map[r.order] = r


            # --- 3. Process Cells ---
            # Efficiently update/create/delete cells based on the final row/column structure

            # Fetch all existing cells for the page *once* for efficient lookup
            existing_cells = Cell.objects.filter(row__page=page)
            # Create a lookup map: {(row_id_str, col_id_str): cell_instance}
            cell_key_map = {(str(cell.row_id), str(cell.column_id)): cell for cell in existing_cells}

            cells_to_update = []
            cells_to_create = []
            # Keep track of cell keys (row_id, col_id) that should exist based on payload
            processed_cell_keys = set()

            # Iterate through the payload rows again to determine cell states
            for i, row_data in enumerate(rows_payload):
                row_order = i + 1
                # Get the corresponding Row instance (should exist in map after row processing)
                if row_order not in final_ordered_rows_map:
                     logger.error(f"Row order {row_order} missing from final map during cell processing for page '{page.slug}'. Save may be inconsistent.")
                     continue # Skip if row instance is missing

                row_instance = final_ordered_rows_map[row_order]
                row_id_str = str(row_instance.id) # Get the row's actual ID (UUID string)

                cell_values = row_data.get('cells', [])
                # Validate cell count again just in case
                if len(cell_values) != len(final_ordered_columns):
                     logger.error(f"Cell count mismatch for row order {row_order} (ID: {row_id_str}) on page '{page.slug}' during cell processing.")
                     raise ValidationError(f"Internal data inconsistency: Row {row_order} cell count error during save.")

                # Iterate through cell values corresponding to the final column order
                for j, cell_value in enumerate(cell_values):
                    # Get the corresponding Column instance based on final order 'j+1'
                    target_col_order = j + 1
                    if target_col_order in final_col_order_map:
                        col_instance = final_col_order_map[target_col_order]
                        col_id_str = str(col_instance.id) # Column ID (UUID string)
                        key = (row_id_str, col_id_str)
                        processed_cell_keys.add(key) # Mark this cell position as expected

                        if key in cell_key_map:
                            # --- Update Existing Cell ---
                            cell = cell_key_map[key]
                            # Only update if the value has actually changed
                            if cell.value != cell_value:
                                cell.value = cell_value
                                cells_to_update.append(cell)
                        else:
                            # --- Prepare New Cell for Creation ---
                            cells_to_create.append(
                                Cell(row=row_instance, column=col_instance, value=cell_value)
                            )
                    else:
                         # This indicates an issue with column processing logic
                         logger.error(f"Column order {target_col_order} not found in final map for row {row_id_str}, page '{page.slug}'.")


            # --- Delete Orphaned Cells ---
            # Find cells existing in the DB but not present in the final structure defined by the payload
            cells_to_delete_ids = [
                cell.id for key, cell in cell_key_map.items() if key not in processed_cell_keys
            ]
            if cells_to_delete_ids:
                deleted_count, _ = Cell.objects.filter(id__in=cells_to_delete_ids).delete()
                logger.debug(f"Deleted {deleted_count} orphaned/unneeded cells for page '{page.slug}'.")

            # --- Perform Bulk Cell Operations ---
            if cells_to_update:
                # Update only the 'value' field for existing cells that changed
                Cell.objects.bulk_update(cells_to_update, ['value'])
                logger.debug(f"Bulk updated {len(cells_to_update)} cells for page '{page.slug}'.")
            if cells_to_create:
                # Create all new cells in one query
                # Ensure row and column FKs are correctly set on the instances before bulk_create
                Cell.objects.bulk_create(cells_to_create)
                logger.debug(f"Bulk created {len(cells_to_create)} cells for page '{page.slug}'.")


            # --- 4. Create Version Snapshot ---
            # Generate the snapshot based on the FINAL state of the database after all updates
            logger.debug(f"Generating final state snapshot for versioning page '{page.slug}'...")
            # Re-fetch final columns and rows with cells for the snapshot
            final_columns_for_snapshot = ColumnSerializer(final_ordered_columns, many=True).data
            final_rows_for_snapshot_data = []
            # Query rows with prefetched cells, ensuring correct ordering for snapshot consistency
            final_rows_queryset = Row.objects.filter(page=page).order_by('order').prefetch_related(
                 Prefetch('cells', queryset=Cell.objects.order_by('column__order')) # Crucial: Order cells by column order
             )
            # Build the snapshot structure matching PageDataSerializer format
            for row in final_rows_queryset:
                 final_rows_for_snapshot_data.append({
                     'id': str(row.id),
                     'order': row.order,
                     'cells': [cell.value for cell in row.cells.all()] # Assumes prefetched cells are correctly ordered
                 })

            # Create the Version record
            Version.objects.create(
                page=page,
                user=request.user,
                data_snapshot={'columns': final_columns_for_snapshot, 'rows': final_rows_for_snapshot_data},
                commit_message=commit_message
            )
            logger.info(f"Created new version snapshot for page '{page.slug}'")

            # Update the page's 'updated_at' timestamp explicitly after all changes
            page.save(update_fields=['updated_at'])


        # End of atomic transaction block
        except ValidationError as e:
            # Catch validation errors raised during processing
            logger.warning(f"Validation error during page save '{page.slug}': {e.detail}", exc_info=True)
            # Re-raise to let DRF handle the 400 response
            raise e
        except IntegrityError as e:
             # Catch potential database integrity errors (e.g., constraint violations)
             logger.error(f"Database integrity error during page save '{page.slug}' by '{request.user.email}': {e}", exc_info=True)
             raise ValidationError("A database conflict occurred while saving. Please check your data and try again.")
        except Exception as e:
            # Catch any other unexpected exceptions during the save process
            logger.error(f"Unexpected error during page save '{page.slug}' by '{request.user.email}': {e}", exc_info=True)
            # Return a generic server error response
            return Response({"error": "An unexpected error occurred while saving the page."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # If transaction completes successfully
        logger.info(f"Page '{page.slug}' saved successfully by '{request.user.email}'.")
        # Return a success message. Frontend should typically re-fetch data for consistency.
        return Response({"message": "Page saved successfully"}, status=status.HTTP_200_OK)


class ColumnWidthUpdateView(views.APIView):
    """ API endpoint specifically for updating column widths efficiently. """
    permission_classes = [permissions.IsAuthenticated, CanEditPage] # Requires EDIT permission

    @transaction.atomic # Use transaction for atomicity if updating multiple columns
    def post(self, request, page_slug):
        """ Handles POST request with a list of column updates. """
        try:
            # Lock the page row to prevent conflicts, although less critical than full save
            page = Page.objects.select_for_update().get(slug=page_slug)
        except Page.DoesNotExist:
            raise NotFound("Page not found.")

        # Check edit permission on the page object
        self.check_object_permissions(request, page)

        # Expect payload like: { "updates": [{ "id": "uuid-str", "width": 180 }, ...] }
        updates = request.data.get('updates')
        if not isinstance(updates, list):
            raise ValidationError({"error": "Invalid data format: 'updates' must be a list."})

        updated_col_ids = []
        errors = []
        columns_to_bulk_update = []
        # Get all valid column IDs for this page upfront for validation
        valid_column_ids = set(page.columns.values_list('id', flat=True))

        for update_data in updates:
            col_id = update_data.get('id')
            width = update_data.get('width')

            # Basic validation for each update item
            if not col_id or width is None:
                errors.append(f"Missing 'id' or 'width' in update item: {update_data}")
                continue
            if not isinstance(col_id, str): # Assuming UUIDs are sent as strings
                 errors.append(f"Invalid column ID format: {col_id}")
                 continue

             # Convert string ID to UUID for lookup (or keep as string if model uses CharField)
            try:
                 col_uuid = uuid.UUID(col_id) # Ensure valid UUID format
                 if col_uuid not in valid_column_ids:
                    errors.append(f"Column with id '{col_id}' not found for this page.")
                    continue
            except ValueError:
                 errors.append(f"Invalid UUID format for column id: {col_id}")
                 continue


            try:
                # Fetch the specific column instance (already validated it belongs to the page)
                column = Column.objects.get(id=col_uuid)
                # Validate width value
                parsed_width = int(width)
                if not (10 <= parsed_width <= 2000): # Define reasonable min/max width limits
                    raise ValueError("Width must be between 10 and 2000 pixels.")

                # Only update if the width has actually changed
                if column.width != parsed_width:
                    column.width = parsed_width
                    columns_to_bulk_update.append(column) # Add to list for bulk update
                updated_col_ids.append(col_id) # Track successfully processed IDs

            except Column.DoesNotExist:
                 # Should not happen if initial validation worked, but handle defensively
                 errors.append(f"Column with id '{col_id}' unexpectedly not found during update.")
            except (ValueError, TypeError) as e:
                errors.append(f"Invalid width value '{width}' for column id '{col_id}': {e}")
            except Exception as e:
                logger.error(f"Error processing width update for col '{col_id}' on page '{page_slug}': {e}", exc_info=True)
                errors.append(f"Internal error updating column '{col_id}'.")

        # If any errors occurred during validation, raise ValidationError to rollback transaction
        if errors:
            logger.warning(f"Column width update failed for page '{page_slug}': {errors}")
            raise ValidationError({"errors": errors})

        # If validation passed and there are columns to update, perform bulk update
        if columns_to_bulk_update:
            try:
                Column.objects.bulk_update(columns_to_bulk_update, ['width'])
                logger.info(f"Updated widths for {len(columns_to_bulk_update)} columns on page '{page_slug}'.")
                # Touch the page's updated_at timestamp
                page.save(update_fields=['updated_at'])
            except Exception as e:
                 # Catch errors during the bulk update itself
                 logger.error(f"Error during bulk update for column widths page '{page_slug}': {e}", exc_info=True)
                 raise ValidationError("Failed to save column width changes due to a database error.")

        # Return success response
        return Response({"message": f"Widths updated for columns: {updated_col_ids}"}, status=status.HTTP_200_OK)


class PageVersionListView(generics.ListAPIView):
     """ API endpoint to list historical versions (snapshots) for a specific page. """
     serializer_class = VersionSerializer       # Use the serializer defined for versions
     permission_classes = [permissions.IsAuthenticated, CanViewPage] # Require VIEW permission on the page
     # pagination_class = None                  # Disable pagination or use a specific pagination class if needed

     def get_queryset(self):
         """ Filter versions belonging to the specified page slug. """
         page_slug = self.kwargs.get('page_slug')
         # Fetch the page object first to check permissions and filter versions
         # Use select_related('owner') if owner info is needed for permission check
         page = get_object_or_404(Page.objects.select_related('owner'), slug=page_slug)

         # Check if the current user has permission to view this page
         self.check_object_permissions(self.request, page)

         logger.debug(f"Listing versions for page '{page_slug}' for user '{self.request.user.email}'")
         # Fetch versions related to this page, ordered by timestamp descending (newest first)
         # Select related user for efficiency when serializing user info
         return Version.objects.filter(page=page).select_related('user').order_by('-timestamp')

# --- Placeholder for Permission Management Views ---
# These would handle CRUD for Groups, adding/removing users from Groups,
# and granting/revoking PagePermissions for users/groups on specific pages.
# They would require careful permission checking (e.g., CanManagePagePermissions).

# class GroupViewSet(viewsets.ModelViewSet):
#     queryset = Group.objects.all()
#     serializer_class = GroupSerializer # Define GroupSerializer
#     permission_classes = [permissions.IsAuthenticated] # Add appropriate permissions

# class PagePermissionView(views.APIView):
#     permission_classes = [permissions.IsAuthenticated, CanManagePagePermissions]
#     # Implement GET (list perms), POST (grant perm), DELETE (revoke perm) for a page
#     pass
