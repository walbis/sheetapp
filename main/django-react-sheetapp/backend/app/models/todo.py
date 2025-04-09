from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
import uuid # Use UUID for ToDo primary key
from .page import Page # Import related Page model
from .structure import Row # Import Row model to link status

class Todo(models.Model):
    """ Represents a ToDo list derived from a specific Page. """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name=_("ToDo Name"))
    # Slug could be unique per user or per source page, depending on requirements.
    # Unique per source page seems more logical here.
    slug = models.SlugField(
        max_length=255,
        blank=True, # Auto-generate
        db_index=True,
        help_text=_("Unique identifier for URL within the source page context (auto-generated)")
    )
    source_page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE, # Deleting the page deletes associated ToDo lists
        related_name='todos',     # Allows page.todos lookup
        verbose_name=_("Source Page")
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, # Deleting user deletes their created ToDo lists (or use SET_NULL?)
        related_name='created_todos', # Allows user.created_todos lookup
        verbose_name=_("Creator")
    )
    # Controls visibility/editability beyond basic page permissions
    is_personal = models.BooleanField(
        default=True,
        verbose_name=_("Personal ToDo"),
        help_text=_("If true, only the creator (and admins) can view/edit this specific ToDo list.")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Slug should be unique within the context of its source page
        unique_together = ('source_page', 'slug')
        ordering = ['-created_at']
        verbose_name = _("ToDo List")
        verbose_name_plural = _("ToDo Lists")

    def save(self, *args, **kwargs):
        """ Auto-generate slug based on name and ensure uniqueness within the source page. """
        from django.utils.text import slugify # Local import for utility
        if not self.slug:
            # Generate base slug from name or use part of UUID as fallback
            base_slug = slugify(self.name) if self.name else f"todo-{str(self.id)[:8]}"
            slug = base_slug
            counter = 1
            # Check uniqueness against other ToDos for the *same source page*
            while Todo.objects.filter(source_page=self.source_page, slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        """ String representation of the ToDo list. """
        personal_marker = "[Personal] " if self.is_personal else ""
        return f"{personal_marker}ToDo '{self.name}' (Page: '{self.source_page.name}')"

    def initialize_statuses(self):
        """
        Creates initial 'Not Started' status entries for each row currently
        present in the source page when the ToDo list is first created.
        Should be called typically right after the Todo instance is saved.
        """
        # Check if statuses already exist to prevent duplication if called multiple times
        if not self.statuses.exists():
            # Get all rows belonging to the source page
            source_rows = self.source_page.rows.all()
            # Prepare status objects for bulk creation
            statuses_to_create = [
                TodoStatus(todo=self, row=row, status=TodoStatus.Status.NOT_STARTED)
                for row in source_rows
            ]
            # Create all status objects in a single database query if any rows exist
            if statuses_to_create:
                TodoStatus.objects.bulk_create(statuses_to_create)
                print(f"Initialized {len(statuses_to_create)} statuses for ToDo '{self.name}'") # Logging/Debug


class TodoStatus(models.Model):
    """ Tracks the status of a specific row from the source page within a ToDo list. """
    # Django automatically creates an 'id' AutoField

    # Define possible status values using TextChoices
    class Status(models.TextChoices):
        NOT_STARTED = 'NOT_STARTED', _('Not Started')
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
        COMPLETED = 'COMPLETED', _('Completed')

    # Link back to the specific ToDo list this status belongs to
    todo = models.ForeignKey(
        Todo,
        on_delete=models.CASCADE, # Deleting the ToDo list deletes its statuses
        related_name='statuses',  # Allows todo.statuses lookup
        verbose_name=_("ToDo List")
    )
    # Link to the original Row in the source Page
    row = models.ForeignKey(
        Row,
        on_delete=models.CASCADE, # Deleting the source row deletes its status entries across all ToDos
        related_name='todo_statuses', # Allows row.todo_statuses lookup
        verbose_name=_("Source Row")
    )
    # The current status of this row within this ToDo list
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NOT_STARTED,
        db_index=True, # Index status for potential filtering
        verbose_name=_("Status")
    )
    updated_at = models.DateTimeField(auto_now=True) # Track when status was last changed

    def clean(self):
        """ Validate that the linked Row belongs to the ToDo's source Page. """
        super().clean()
        # Check only if both foreign keys are already set (avoid errors during initial form creation)
        if hasattr(self, 'row') and hasattr(self, 'todo') and self.row and self.todo:
             if self.row.page != self.todo.source_page:
                 raise ValidationError(
                     _("Invalid Row: The selected row (ID: %(row_id)s, Order: %(row_order)s) does not belong to the ToDo's source page (%(page_name)s)."),
                     code='invalid_row_for_todo',
                     params={'row_id': self.row.id, 'row_order': self.row.order, 'page_name': self.todo.source_page.name}
                 )

    class Meta:
        # Ensure only one status entry exists per ToDo list and source Row combination
        unique_together = ('todo', 'row')
        # Order statuses based on the source row's order by default
        ordering = ['row__order']
        verbose_name = _("ToDo Status")
        verbose_name_plural = _("ToDo Statuses")
        indexes = [
            models.Index(fields=['todo', 'row']), # Index for unique constraint and lookups
        ]

    def __str__(self):
        """ String representation of the ToDo status. """
        try:
            row_order = self.row.order
            return f"Status for ToDo '{self.todo.name}' - Row {row_order}: {self.get_status_display()}"
        except Row.DoesNotExist:
            return f"Orphaned Status for ToDo '{self.todo.name}'"
        except Todo.DoesNotExist:
             return f"Orphaned Status for Row {self.row_id}"
