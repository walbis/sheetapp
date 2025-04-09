from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from .page import Page # Import related Page model

class Version(models.Model):
    """
    Represents a historical snapshot of a Page's structure and data.
    Created whenever a user saves changes to a page.
    """
    # Use BigAutoField for primary key as there could be many versions per page over time
    id = models.BigAutoField(primary_key=True)
    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE, # Deleting a page deletes its versions
        related_name='versions',  # Allows page.versions lookup
        verbose_name=_("Page")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True, # Allow null if changes are made by the system or anonymous (if applicable)
        on_delete=models.SET_NULL, # Keep version history even if user is deleted, just unlink user
        related_name='page_versions', # Allows user.page_versions lookup
        verbose_name=_("User")
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Timestamp"))
    # JSONField stores the snapshot of the page state (columns, rows, cell values)
    # This avoids complex relational history tracking but requires careful serialization/deserialization.
    data_snapshot = models.JSONField(verbose_name=_("Data Snapshot"))
    # Example snapshot structure (defined in comments for clarity):
    # {
    #   "columns": [{"id": "uuid-string", "name": "Col A", "order": 1, "width": 150}, ...],
    #   "rows": [
    #       {"id": "uuid-string", "order": 1, "cells": ["Value R1C1", "Value R1C2", ...]}, # Cell values in column order
    #       {"id": "uuid-string", "order": 2, "cells": ["Value R2C1", "Value R2C2", ...]},
    #       ...
    #   ]
    # }
    commit_message = models.TextField(blank=True, verbose_name=_("Commit Message (Optional)"))

    class Meta:
        ordering = ['-timestamp'] # Show newest versions first by default
        verbose_name = _("Page Version")
        verbose_name_plural = _("Page Versions")
        # Indexing page and timestamp improves query performance for version history lookups
        indexes = [
            models.Index(fields=['page', '-timestamp']),
        ]

    def __str__(self):
        """ String representation of the Version model. """
        user_identifier = self.user.email if self.user else "System/Unknown"
        # Format timestamp for readability
        formatted_timestamp = self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        return f"Version for '{self.page.name}' at {formatted_timestamp} by {user_identifier}"
