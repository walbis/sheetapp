from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from .page import Page # Import Page model

# Model for User Groups
class Group(models.Model):
    """ Represents a group of users for assigning permissions collectively. """
    # Django automatically creates an 'id' AutoField (BigAutoField by default settings)
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Group Name"))
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, # Or PROTECT if groups shouldn't be deleted when owner is
        related_name='owned_groups', # Allows user.owned_groups lookup
        verbose_name=_("Group Owner")
    )
    # ManyToManyField defines the relationship between Groups and Users
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='UserGroupMembership', # Specify the intermediate model
        related_name='member_of_groups', # Allows user.member_of_groups lookup
        verbose_name=_("Members"),
        blank=True # A group can exist without members initially
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("User Group")
        verbose_name_plural = _("User Groups")
        ordering = ['name'] # Order groups alphabetically by name

    def __str__(self):
        """ String representation of the Group model. """
        return self.name

# Intermediate model for the ManyToMany relationship between User and Group
# This allows adding extra fields to the membership relation if needed (e.g., date_joined)
class UserGroupMembership(models.Model):
    """ Represents the membership of a User in a Group. """
    # Django automatically creates an 'id' AutoField
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name=_("Date Joined"))

    class Meta:
        # Ensure a user can only be added to a group once
        unique_together = ('user', 'group')
        verbose_name = _("User Group Membership")
        verbose_name_plural = _("User Group Memberships")
        ordering = ['group__name', 'user__email']

    def __str__(self):
        return f"{self.user.email} in {self.group.name}"


# Model for Page-Specific Permissions
class PagePermission(models.Model):
    """ Assigns specific permission levels for a Page to users or groups. """
    # Django automatically creates an 'id' AutoField

    # Define available permission levels using TextChoices for better readability and validation
    class Level(models.TextChoices):
        VIEW = 'VIEW', _('View')     # Can see the page content
        EDIT = 'EDIT', _('Edit')     # Can modify content and structure
        MANAGE = 'MANAGE', _('Manage Permissions') # Can grant/revoke permissions to others

    # Define the types of targets a permission can apply to
    class TargetType(models.TextChoices):
        PUBLIC = 'PUBLIC', _('Public')         # Applies to everyone, including anonymous users
        USER = 'USER', _('Specific User')      # Applies to a single specified user
        GROUP = 'GROUP', _('Specific Group')   # Applies to all members of a specified group

    # Foreign Key to the Page this permission applies to
    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE, # Deleting page removes its permissions
        related_name='permissions', # Allows page.permissions lookup
        verbose_name=_("Page")
    )
    # The permission level being granted (VIEW, EDIT, MANAGE)
    level = models.CharField(max_length=10, choices=Level.choices, verbose_name=_("Permission Level"))
    # The type of entity this permission targets (PUBLIC, USER, GROUP)
    target_type = models.CharField(max_length=10, choices=TargetType.choices, verbose_name=_("Target Type"))

    # Foreign Key to a specific User (used only if target_type is USER)
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.CASCADE, # Deleting user removes their specific permissions
        related_name='page_permissions', # Allows user.page_permissions lookup
        verbose_name=_("Target User")
    )
    # Foreign Key to a specific Group (used only if target_type is GROUP)
    target_group = models.ForeignKey(
        Group, null=True, blank=True,
        on_delete=models.CASCADE, # Deleting group removes its permissions
        related_name='page_permissions', # Allows group.page_permissions lookup
        verbose_name=_("Target Group")
    )

    # Optional fields to track who granted the permission and when
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, # Keep record even if granter deleted
        related_name='granted_permissions',
        verbose_name=_("Granted By")
    )
    granted_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Granted At"))

    def clean(self):
        """ Add model-level validation logic. """
        super().clean()
        # Ensure target consistency based on target_type
        if self.target_type == self.TargetType.PUBLIC:
            if self.target_user or self.target_group:
                raise ValidationError(_("Public permissions cannot target a specific user or group."))
            # Enforce that PUBLIC only applies to VIEW level (adjust if needed)
            if self.level != self.Level.VIEW:
                 raise ValidationError(_("Public permissions currently only support the 'View' level."))
        elif self.target_type == self.TargetType.USER:
            if not self.target_user:
                raise ValidationError(_("Permission type 'User' requires a specific target user to be selected."))
            if self.target_group:
                raise ValidationError(_("Permission type 'User' cannot target a group."))
        elif self.target_type == self.TargetType.GROUP:
             if not self.target_group:
                 raise ValidationError(_("Permission type 'Group' requires a specific target group to be selected."))
             if self.target_user:
                raise ValidationError(_("Permission type 'Group' cannot target a user."))

    class Meta:
        # Ensure a unique combination of page, level, target type, user, and group
        # This prevents granting the exact same permission multiple times.
        unique_together = ('page', 'level', 'target_type', 'target_user', 'target_group')
        verbose_name = _("Page Permission")
        verbose_name_plural = _("Page Permissions")
        ordering = ['page__name', 'level']
        # Optional: Add DB constraints for target consistency if your DB supports them well
        # constraints = [
        #     models.CheckConstraint(...)
        # ]

    def __str__(self):
        """ String representation showing the permission details. """
        target = self.get_target_type_display() # Get display name for target type
        if self.target_type == self.TargetType.USER and self.target_user:
            target = self.target_user.email # Show user email if target is user
        elif self.target_type == self.TargetType.GROUP and self.target_group:
            target = self.target_group.name # Show group name if target is group
        # Example: "Page 'My Report' - Edit for group 'Editors'"
        return f"Page '{self.page.name}' - {self.get_level_display()} for {target}"
