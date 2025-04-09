from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.urls import reverse
from django.utils.html import format_html
from .models import (
    User, Page, Column, Row, Cell, Version, Todo, TodoStatus,
    Group, UserGroupMembership, PagePermission
)

# Customize UserAdmin to use email and show relevant fields
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    # Use email for login field in admin if needed, but default UserAdmin structure is fine
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    filter_horizontal = ('groups', 'user_permissions',) # Makes selecting groups/perms easier

# Inlines for related models to show them within parent admin pages

class ColumnInline(admin.TabularInline):
    model = Column
    extra = 1 # Show one extra blank row for adding
    ordering = ('order',)
    fields = ('name', 'order', 'width') # Control displayed fields

class RowInline(admin.TabularInline):
    model = Row
    extra = 1 # Show one extra blank row for adding
    ordering = ('order',)
    show_change_link = True # Allows clicking to edit row details (e.g., cells via RowAdmin)
    fields = ('order',) # Only show order in this inline view

class CellInline(admin.TabularInline):
    model = Cell
    extra = 0 # Don't show extra cell inlines by default, manage via RowAdmin detail
    fields = ('column', 'value')
    raw_id_fields = ('column',) # Use search popup for columns if many exist
    ordering = ('column__order',) # Order cells by column order

class PagePermissionInline(admin.TabularInline):
    model = PagePermission
    extra = 1 # Show one extra row for adding permissions
    fields = ('level', 'target_type', 'target_user', 'target_group')
    raw_id_fields = ('target_user', 'target_group') # Use search popups
    # 'granted_by' will be set automatically if needed, not shown here

class TodoStatusInline(admin.TabularInline):
    model = TodoStatus
    extra = 0 # Usually statuses are initialized automatically, not added manually
    fields = ('row_link', 'status', 'updated_at')
    readonly_fields = ('updated_at', 'row_link') # Make fields read-only in inline
    raw_id_fields = ('row',) # Use search popup for rows

    # Custom method to display a link to the related row admin page
    def row_link(self, obj):
         if obj.row_id: # Check if row exists
             link = reverse("admin:app_row_change", args=[obj.row.id])
             return format_html('Row <a href="{}">{}</a>', link, obj.row.order)
         return "N/A"
    row_link.short_description = 'Source Row'

class UserGroupMembershipInline(admin.TabularInline):
    model = UserGroupMembership
    extra = 1
    raw_id_fields = ('user',)
    verbose_name = "Member"
    verbose_name_plural = "Members"


# ModelAdmin definitions

@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'owner_link', 'created_at', 'updated_at')
    search_fields = ('name', 'slug', 'owner__email', 'owner__username')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ColumnInline, RowInline, PagePermissionInline] # Manage related objects inline
    raw_id_fields = ('owner',)
    list_filter = ('owner__email',) # Filter by owner's email
    date_hierarchy = 'created_at'
    list_select_related = ('owner',) # Optimize owner lookup

    # Custom method to display owner as a link
    def owner_link(self, obj):
        if obj.owner:
             link = reverse("admin:app_user_change", args=[obj.owner.id])
             return format_html('<a href="{}">{}</a>', link, obj.owner.email)
        return "-"
    owner_link.short_description = 'Owner'


@admin.register(Row)
class RowAdmin(admin.ModelAdmin):
    inlines = [CellInline] # Manage Cells directly within the Row view
    list_display = ('id', 'page_link', 'order', 'created_at')
    list_filter = ('page__name',) # Filter by page name directly
    search_fields = ('page__name', 'page__slug', 'id') # Allow searching by row UUID
    list_select_related = ('page',) # Optimize page lookup
    ordering = ('page__name', 'order') # Default ordering

    # Custom method to display page as a link
    def page_link(self, obj):
        link = reverse("admin:app_page_change", args=[obj.page.id])
        return format_html('<a href="{}">{}</a>', link, obj.page.name)
    page_link.short_description = 'Page'


@admin.register(Version)
class VersionAdmin(admin.ModelAdmin):
    list_display = ('id', 'page_link', 'user_link', 'timestamp', 'commit_message_short')
    list_filter = ('page__name', 'user__email')
    date_hierarchy = 'timestamp' # Allow easy date filtering
    raw_id_fields = ('page', 'user') # Use search popup for FKs
    list_select_related = ('page', 'user') # Optimize FK lookups
    search_fields = ('page__name', 'user__email', 'commit_message')
    readonly_fields = ('timestamp', 'data_snapshot') # Snapshot is usually read-only

    # Link to Page
    def page_link(self, obj):
        link = reverse("admin:app_page_change", args=[obj.page.id])
        return format_html('<a href="{}">{}</a>', link, obj.page.name)
    page_link.short_description = 'Page'

    # Link to User
    def user_link(self, obj):
        if obj.user:
             link = reverse("admin:app_user_change", args=[obj.user.id])
             return format_html('<a href="{}">{}</a>', link, obj.user.email)
        return "System" # Or Anonymous if applicable
    user_link.short_description = 'User'

    # Shorten commit message for display
    def commit_message_short(self, obj):
        limit = 75
        return (obj.commit_message[:limit] + '...') if len(obj.commit_message) > limit else obj.commit_message
    commit_message_short.short_description = 'Commit Message'


@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    list_display = ('name', 'source_page_link', 'creator_link', 'is_personal', 'created_at')
    search_fields = ('name', 'source_page__name', 'creator__email')
    list_filter = ('is_personal', 'source_page__name', 'creator__email')
    inlines = [TodoStatusInline] # Manage statuses inline
    raw_id_fields = ('source_page', 'creator')
    list_select_related = ('source_page', 'creator') # Optimize FK lookups
    date_hierarchy = 'created_at'
    readonly_fields = ('slug', 'created_at', 'updated_at') # Slug is auto-generated

    # Link to Source Page
    def source_page_link(self, obj):
         link = reverse("admin:app_page_change", args=[obj.source_page.id])
         return format_html('<a href="{}">{}</a>', link, obj.source_page.name)
    source_page_link.short_description = 'Source Page'

    # Link to Creator
    def creator_link(self, obj):
         link = reverse("admin:app_user_change", args=[obj.creator.id])
         return format_html('<a href="{}">{}</a>', link, obj.creator.email)
    creator_link.short_description = 'Creator'


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner_link', 'member_count')
    search_fields = ('name', 'owner__email')
    inlines = [UserGroupMembershipInline] # Manage members inline
    raw_id_fields = ('owner',)
    list_select_related = ('owner',) # Optimize owner lookup

    # Link to Owner
    def owner_link(self, obj):
         link = reverse("admin:app_user_change", args=[obj.owner.id])
         return format_html('<a href="{}">{}</a>', link, obj.owner.email)
    owner_link.short_description = 'Owner'

    # Calculate member count
    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Members'

# Register the custom User admin
admin.site.register(User, UserAdmin)

# Other models are registered using the @admin.register decorator above
# Models managed via inlines (Column, Cell, PagePermission, TodoStatus, UserGroupMembership)
# do not need separate registration unless you want a dedicated admin page for them.