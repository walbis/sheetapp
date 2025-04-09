# This file makes the 'serializers' directory a Python package.
# It allows easier importing of serializers.
# e.g., from app.serializers import PageListSerializer

from .user_serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer, UserBasicSerializer
)
from .page_serializers import (
    PageListSerializer, PageDetailSerializer, PageDataSerializer, VersionSerializer,
    ColumnSerializer, RowSerializer, CellSerializer # If needed directly
)
from .todo_serializers import (
    TodoListSerializer, TodoDetailSerializer, TodoCreateSerializer,
    TodoStatusSerializer, TodoStatusUpdateSerializer
)
# Add Group and Permission serializers later if needed
# from .permission_serializers import GroupSerializer, PagePermissionSerializer

# Define __all__ to control wildcard imports
__all__ = [
    # User Serializers
    'UserSerializer', 'RegisterSerializer', 'LoginSerializer', 'UserBasicSerializer',
    # Page Serializers
    'PageListSerializer', 'PageDetailSerializer', 'PageDataSerializer', 'VersionSerializer',
    'ColumnSerializer', 'RowSerializer', 'CellSerializer',
    # ToDo Serializers
    'TodoListSerializer', 'TodoDetailSerializer', 'TodoCreateSerializer',
    'TodoStatusSerializer', 'TodoStatusUpdateSerializer',
    # Permission Serializers (Add when created)
    # 'GroupSerializer', 'PagePermissionSerializer',
]