import logging
from rest_framework import serializers
# Import necessary models, including PagePermission
from ..models import Todo, TodoStatus, Page, Row, PagePermission
from .user_serializers import UserBasicSerializer
from .page_serializers import PageListSerializer # Embed basic page info if needed
# Import check_permission helper function (adjust path if it's moved to utils)
from ..permissions import check_permission

logger = logging.getLogger(__name__)


class TodoStatusSerializer(serializers.ModelSerializer):
    # FIX: Removed redundant source='id' (if present)
    id = serializers.CharField(read_only=True) # Represent BigAutoField as string
    row_id = serializers.CharField(source='row.id', read_only=True) # Send row UUID string
    row_order = serializers.IntegerField(source='row.order', read_only=True) # Send row number

    class Meta:
        model = TodoStatus
        fields = ['id', 'row_id', 'row_order', 'status', 'updated_at']
        read_only_fields = ['id', 'row_id', 'row_order', 'updated_at'] # Only status is writable via dedicated endpoint

class TodoListSerializer(serializers.ModelSerializer):
    # FIX: Removed redundant source='id'
    id = serializers.CharField(read_only=True) # Represent UUID as string
    creator = UserBasicSerializer(read_only=True)
    source_page_slug = serializers.SlugRelatedField(source='source_page', slug_field='slug', read_only=True)
    source_page_name = serializers.CharField(source='source_page.name', read_only=True) # Include name for display

    class Meta:
        model = Todo
        fields = ['id', 'name', 'slug', 'source_page_slug', 'source_page_name', 'creator', 'is_personal', 'created_at']


class TodoDetailSerializer(serializers.ModelSerializer):
    # FIX: Removed redundant source='id'
    id = serializers.CharField(read_only=True) # Represent UUID as string
    creator = UserBasicSerializer(read_only=True)
    source_page = PageListSerializer(read_only=True) # Embed basic page info
    statuses = TodoStatusSerializer(many=True, read_only=True, source='statuses.all') # Use source for ordered related manager

    class Meta:
        model = Todo
        fields = [
            'id', 'name', 'slug', 'source_page', 'creator', 'is_personal',
            'statuses', 'created_at', 'updated_at'
        ]
        read_only_fields = fields # ToDo details are read-only, updates via specific actions/serializers


class TodoCreateSerializer(serializers.ModelSerializer):
    # This field is only used for input validation and linking in the view/serializer create
    source_page_slug = serializers.SlugField(write_only=True, required=True, help_text="Slug of the page to base this ToDo list on.")

    class Meta:
        model = Todo
        # Exclude source_page here, it will be set in create method from context/save() call
        # Slug is also excluded as it's auto-generated
        fields = ['name', 'is_personal', 'source_page_slug']
        extra_kwargs = {
            'name': {'required': True, 'allow_blank': False},
            'is_personal': {'required': False}, # Defaults to True in model
        }

    def validate_source_page_slug(self, value):
        """ Validate slug and check user permission to view the source page. """
        try:
            page = Page.objects.select_related('owner').get(slug=value) # Fetch owner for permission check efficiency
        except Page.DoesNotExist:
            raise serializers.ValidationError("Source page not found.")

        request = self.context.get('request')
        if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
             raise serializers.ValidationError("User context is missing or user is not authenticated.")

        user = request.user
        # Use the imported check_permission function and PagePermission model
        if not check_permission(user, page, PagePermission.Level.VIEW): # Use imported PagePermission
            raise serializers.ValidationError("You do not have permission to view the source page to create a ToDo list from it.")

        # Attach page instance to context for use in the view's perform_create or serializer create
        self.context['source_page_instance'] = page
        return value

    # --- Override the create method ---
    def create(self, validated_data):
        """
        Override create to handle 'source_page_slug' correctly.
        We expect 'creator' and 'source_page' (model instance) to be passed via
        serializer.save() call context in the view.
        """
        # Remove the write_only slug field before passing to Model.objects.create
        # It was only needed for validation.
        validated_data.pop('source_page_slug', None)

        # 'creator' and 'source_page' should be in validated_data because they
        # were passed into serializer.save(creator=..., source_page=...) in the view.
        # DRF automatically includes extra kwargs from .save() into validated_data passed to .create().
        if 'creator' not in validated_data:
             logger.error("TodoCreateSerializer create error: 'creator' missing in validated_data. Was it passed in view's serializer.save()?")
             raise serializers.ValidationError("Creator must be provided during save.")
        if 'source_page' not in validated_data:
             logger.error("TodoCreateSerializer create error: 'source_page' instance missing in validated_data. Was it passed in view's serializer.save()?")
             raise serializers.ValidationError("Source Page must be provided during save.")

        logger.debug(f"TodoCreateSerializer attempting to create Todo with data: { {k:v for k,v in validated_data.items() if k != 'creator'} } for creator {validated_data['creator'].email}") # Avoid logging sensitive user details if any
        try:
            # Create the Todo instance using the remaining validated data
            # (which now includes creator and source_page instance)
            instance = Todo.objects.create(**validated_data)
            logger.info(f"Todo instance created successfully: {instance.id}")
            return instance
        except TypeError as e:
            # Catch potential TypeErrors during object creation if arguments mismatch
             logger.error(f"TypeError during Todo.objects.create: {e}", exc_info=True)
             msg = (
                'Got a `TypeError` when calling `Todo.objects.create()`. '
                'Check that all required fields (`name`, `creator`, `source_page`) are provided correctly to the '
                'serializer\'s save() method in the view, and that `source_page` is a Page instance.\nOriginal exception was: %s' % e
             )
             raise TypeError(msg) # Re-raise with DRF context


class TodoStatusUpdateSerializer(serializers.Serializer):
    """ Serializer just for validating the status update payload. """
    status = serializers.ChoiceField(choices=TodoStatus.Status.choices, required=True)
