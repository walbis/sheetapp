import logging # Import logging
from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import Page, Column, Row, Cell, Version # Import relevant models
from .user_serializers import UserBasicSerializer # Import basic user info serializer

# Get logger instance
logger = logging.getLogger(__name__)
User = get_user_model()

# --- Basic Component Serializers ---

class ColumnSerializer(serializers.ModelSerializer):
    """ Serializer for representing Column structure. """
    # FIX: Removed redundant source='id'
    id = serializers.CharField(read_only=True)

    class Meta:
        model = Column
        fields = ['id', 'name', 'order', 'width']
        read_only_fields = ['id']


class CellSerializer(serializers.ModelSerializer):
    """
    Serializer for Cell instances. Typically used internally or for detailed debugging.
    """
    # FIX: Removed redundant source='id' (assuming implicit handling or specific field name 'id')
    id = serializers.CharField(read_only=True)
    column_id = serializers.CharField(source='column.id', read_only=True)
    row_id = serializers.CharField(source='row.id', read_only=True)

    class Meta:
        model = Cell
        fields = ['id', 'value', 'column_id', 'row_id', 'updated_at']


class RowSerializer(serializers.ModelSerializer):
    """ Serializer for Row instances (metadata like order). """
    # FIX: Removed redundant source='id'
    id = serializers.CharField(read_only=True)

    class Meta:
        model = Row
        fields = ['id', 'order']
        read_only_fields = ['id']


# --- Page List and Detail Serializers (Metadata) ---

class PageListSerializer(serializers.ModelSerializer):
    """ Serializer specifically for listing multiple pages efficiently. """
    # FIX: Removed redundant source='id'
    id = serializers.CharField(read_only=True)
    owner = UserBasicSerializer(read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name='page-detail', lookup_field='slug')

    class Meta:
        model = Page
        fields = ['id', 'name', 'slug', 'owner', 'created_at', 'updated_at', 'url']


class PageDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing/creating/updating basic page information (like name).
    Does NOT handle the full cell data save/retrieve.
    """
    # FIX: Removed redundant source='id'
    id = serializers.CharField(read_only=True)
    owner = UserBasicSerializer(read_only=True)
    columns = ColumnSerializer(many=True, read_only=True, source='columns.all')

    class Meta:
        model = Page
        fields = ['id', 'name', 'slug', 'owner', 'columns', 'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'owner', 'columns', 'created_at', 'updated_at']
        extra_kwargs = {
            'name': {'required': True, 'allow_blank': False, 'max_length': 255}
        }


# --- Serializers for Handling Full Page Data (Structure + Cells) ---

class PageDataColumnSerializer(serializers.Serializer):
    """ Represents a single column within the PageDataSerializer payload. """
    # FIX: Removed redundant source='id' (if it was present)
    id = serializers.CharField(required=False, allow_null=True)
    name = serializers.CharField(max_length=100, required=True, allow_blank=False)
    order = serializers.IntegerField(min_value=1)
    width = serializers.IntegerField(default=150, min_value=10, max_value=2000)


class PageDataRowSerializer(serializers.Serializer):
    """ Represents a single row within the PageDataSerializer payload. """
    # FIX: Removed redundant source='id' (if it was present)
    id = serializers.CharField(required=False, allow_null=True)
    order = serializers.IntegerField(min_value=1)
    cells = serializers.ListField(
        # *** FIX: Ensure child CharField explicitly allows blank values ***
        child=serializers.CharField(allow_blank=True),
        required=True,
        allow_empty=True # Allow rows with zero cells if columns are zero
    )


class PageDataSerializer(serializers.Serializer):
    """
    Serializer used by PageDataView (retrieve) and PageSaveView (post).
    Handles the full structure: columns, rows, and cell values.
    """
    # Fields included when retrieving full page data
    # FIX: Removed redundant source='id'
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    slug = serializers.SlugField(read_only=True)
    owner = UserBasicSerializer(read_only=True)

    # Fields used for both retrieving and saving (payload structure)
    columns = PageDataColumnSerializer(many=True)
    rows = PageDataRowSerializer(many=True)

    # Field only used when saving (POST request payload)
    commit_message = serializers.CharField(
        required=False, allow_blank=True, write_only=True, max_length=500,
        help_text="Optional message describing the changes made."
    )

    def validate_columns(self, columns_data):
        """ Validates the list of column objects in the save payload. """
        if not columns_data:
            raise serializers.ValidationError("Page must have at least one column.")
        orders = sorted([col['order'] for col in columns_data])
        expected_orders = list(range(1, len(columns_data) + 1))
        if orders != expected_orders:
            raise serializers.ValidationError(f"Column orders must be unique and sequential from 1 to {len(columns_data)}. Received orders: {orders}")
        names_lower = [col['name'].lower() for col in columns_data]
        if len(names_lower) != len(set(names_lower)):
            raise serializers.ValidationError("Column names must be unique (case-insensitive).")
        return columns_data

    def validate_rows(self, rows_data):
        """ Validates the list of row objects in the save payload. """
        if not rows_data:
             return [] # Allow saving with zero rows
        orders = sorted([row['order'] for row in rows_data])
        expected_orders = list(range(1, len(rows_data) + 1))
        if orders != expected_orders:
            raise serializers.ValidationError(f"Row orders must be unique and sequential from 1 to {len(rows_data)}. Received orders: {orders}")
        return rows_data

    # --- Overwrite validate method with added logging ---
    def validate(self, data):
        """
        Performs cross-field validation after individual field validation.
        Ensures the number of cells in each row matches the number of columns defined.
        """
        columns = data.get('columns', [])
        rows = data.get('rows', [])
        num_columns = len(columns)
        logger.debug(f"PageDataSerializer validate: Num columns = {num_columns}, Num rows = {len(rows)}")

        for i, row in enumerate(rows):
            row_cells = row.get('cells')
            # Log the type and content of cells being validated
            logger.debug(f"Validating row index {i} (Order: {row.get('order')}): Cells data type = {type(row_cells)}, Content = {row_cells}")

            # Check if 'cells' is actually a list
            if not isinstance(row_cells, list):
                logger.error(f"Validation Error in row {i}: 'cells' is not a list, it's a {type(row_cells)}. Data: {row_cells}")
                # Raise a more specific error related to the row structure
                raise serializers.ValidationError({
                    f"rows[{i}]": f"Invalid format: 'cells' must be a list."
                })

            # Check if the number of cells matches the number of columns
            if len(row_cells) != num_columns:
                 logger.error(f"Validation Error in row {i}: Cell count mismatch. Expected {num_columns}, got {len(row_cells)}. Row Data: {row}")
                 raise serializers.ValidationError({
                     f"rows[{i}].cells": f"Incorrect number of cells. Expected {num_columns}, got {len(row_cells)}."
                 })

            # The 'allow_blank=True' on the ListField's child CharField *should* handle blank strings.
            # If the 'This field may not be blank' error still appears, it suggests either:
            # 1. The payload isn't sending strings (e.g., sending `null`). Check frontend Network tab Request Payload.
            # 2. A complex interaction with DRF validation isn't respecting allow_blank in this nested context.
            # We rely on the ListField's child validation here. Explicit checks below are for extreme debugging.
            # for j, cell_value in enumerate(row_cells):
            #     if cell_value == "" and not serializers.CharField(allow_blank=True).allow_blank: # Simulate check
            #         logger.critical(f"INTERNAL VALIDATION MISMATCH?: Cell [{i},{j}] is blank but allow_blank check failed.")

        logger.debug("PageDataSerializer cross-field validation passed.")
        return data


# --- Version Serializer ---

class VersionSerializer(serializers.ModelSerializer):
    """ Serializer for representing historical Page Versions (snapshots). """
    # FIX: Removed redundant source='id'
    id = serializers.CharField(read_only=True)
    user = UserBasicSerializer(read_only=True)
    page_slug = serializers.SlugRelatedField(source='page', slug_field='slug', read_only=True)

    class Meta:
        model = Version
        fields = [
            'id',
            'page_slug',
            'user',
            'timestamp',
            'commit_message',
            'data_snapshot' # The actual snapshot data (can be large)
        ]
        read_only_fields = fields # Versions are immutable via API
