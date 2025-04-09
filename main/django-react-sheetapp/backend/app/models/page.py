from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
import uuid # Using UUID for primary keys is good practice

class Page(models.Model):
    """ Represents a single sheet or page within the application. """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name=_("Page Name"))
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True, # Allow blank, will be auto-generated
        db_index=True, # Index slug for faster lookups
        help_text=_("Unique identifier for URL (leave blank to auto-generate from name)")
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, # Or models.PROTECT/SET_NULL if pages shouldn't be deleted when owner is
        related_name='owned_pages', # Allows user.owned_pages lookup
        verbose_name=_("Owner")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Last Updated"))
    # Permissions are handled by the separate PagePermission model

    class Meta:
        verbose_name = _("Page")
        verbose_name_plural = _("Pages")
        ordering = ['-updated_at', '-created_at'] # Default ordering: most recently updated first

    def save(self, *args, **kwargs):
        """ Overrides save method to auto-generate slug if not provided. """
        if not self.slug:
            # Generate base slug from name or use part of UUID as fallback
            base_slug = slugify(self.name) if self.name else f"page-{str(self.id)[:8]}"
            # Ensure slug uniqueness
            slug = base_slug
            counter = 1
            # Check if a page with this slug already exists (excluding self if updating)
            while Page.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs) # Call the original save method

    def __str__(self):
        """ String representation of the Page model. """
        return self.name

    def setup_default_structure(self):
        """
        Creates the default initial structure for a new page (e.g., two columns).
        Called typically after a new Page instance is created.
        """
        # Import models locally to avoid potential circular dependencies at module load time
        from .structure import Column, Row
        # from .data import Cell # Uncomment if creating default cells too

        # Check if columns already exist for this page to prevent duplication
        if not self.columns.exists():
            # Use bulk_create for efficiency if creating multiple objects
            Column.objects.bulk_create([
                Column(page=self, name=_("Column A"), order=1, width=150),
                Column(page=self, name=_("Column B"), order=2, width=150)
            ])
            # Optionally create one default row as well
            # default_row = Row.objects.create(page=self, order=1)
            # Optionally create empty cells for the default row and default columns
            # col_a = self.columns.get(order=1)
            # col_b = self.columns.get(order=2)
            # Cell.objects.bulk_create([
            #     Cell(row=default_row, column=col_a, value=''),
            #     Cell(row=default_row, column=col_b, value=''),
            # ])
            print(f"Default structure created for page '{self.slug}'") # Logging/Debug output
