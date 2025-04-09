from django.db import models
from django.utils.translation import gettext_lazy as _
from .structure import Row, Column # Import related structure models

class Cell(models.Model):
    """ Represents a single cell at the intersection of a Row and Column. """
    # Django automatically creates an 'id' AutoField (BigAutoField by default settings)
    # No need for UUID here unless specifically required for cell identification outside row/col context
    row = models.ForeignKey(
        Row,
        on_delete=models.CASCADE, # Deleting a row deletes its cells
        related_name='cells',     # Allows row.cells lookup
        verbose_name=_("Row")
    )
    column = models.ForeignKey(
        Column,
        on_delete=models.CASCADE, # Deleting a column deletes its cells
        related_name='cells',     # Allows column.cells lookup
        verbose_name=_("Column")
    )
    # TextField allows for potentially large amounts of text in a cell
    value = models.TextField(blank=True, default='', verbose_name=_("Cell Value"))
    # Track when the cell value was last updated
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Last Updated"))

    class Meta:
        # Ensure only one cell exists per row/column combination
        unique_together = ('row', 'column')
        # Default ordering useful for fetching cells in a predictable sequence
        ordering = ['row__order', 'column__order']
        verbose_name = _("Cell")
        verbose_name_plural = _("Cells")
        # Indexing the foreign keys can improve lookup performance, especially for large tables
        indexes = [
            models.Index(fields=['row', 'column']), # Composite index
        ]

    def __str__(self):
        """ String representation of the Cell model, showing coordinates and partial value. """
        # Accessing row.order and column.order might involve extra queries if not select_related/prefetched
        # Be mindful in performance-critical code.
        try:
            row_order = self.row.order
            col_order = self.column.order
            val_preview = (self.value[:20] + '...') if len(self.value) > 20 else self.value
            return f"Cell(R{row_order}, C{col_order}): '{val_preview}'"
        except (Row.DoesNotExist, Column.DoesNotExist):
            # Handle cases where related objects might be missing (shouldn't normally happen with cascade delete)
            return f"Orphaned Cell(ID:{self.id})"
