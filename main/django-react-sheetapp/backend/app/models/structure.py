from django.db import models
from django.utils.translation import gettext_lazy as _
from .page import Page # Import related Page model
import uuid # Use UUID for primary keys

class Column(models.Model):
    """ Represents a single column within a Page. """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE, # Deleting a page deletes its columns
        related_name='columns',   # Allows page.columns lookup
        verbose_name=_("Page")
    )
    name = models.CharField(max_length=100, verbose_name=_("Column Name"))
    # PositiveIntegerField ensures order starts from 1 and is non-negative
    order = models.PositiveIntegerField(verbose_name=_("Display Order"), db_index=True) # Index order for sorting performance
    width = models.PositiveIntegerField(default=150, verbose_name=_("Column Width (px)"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order'] # Default ordering by the 'order' field
        unique_together = ('page', 'order') # Order must be unique within a specific page
        verbose_name = _("Column")
        verbose_name_plural = _("Columns")

    def __str__(self):
        """ String representation of the Column model. """
        return f"Page '{self.page.name}' - Col {self.order}: {self.name}"

class Row(models.Model):
    """ Represents a single row within a Page. """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE, # Deleting a page deletes its rows
        related_name='rows',      # Allows page.rows lookup
        verbose_name=_("Page")
    )
    # PositiveIntegerField ensures row number is positive
    order = models.PositiveIntegerField(verbose_name=_("Row Order"), db_index=True) # Index order for sorting performance
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order'] # Default ordering by the 'order' field (row number)
        unique_together = ('page', 'order') # Order must be unique within a specific page
        verbose_name = _("Row")
        verbose_name_plural = _("Rows")

    def __str__(self):
        """ String representation of the Row model. """
        return f"Page '{self.page.name}' - Row {self.order}"
