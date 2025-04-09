from django.test import TestCase
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from ..models import Page, Group, PagePermission
from ..permissions import check_permission, CanViewPage, CanEditPage, CanManagePagePermissions # Import your permission logic

User = get_user_model()

class PermissionLogicTests(TestCase):
    """ Tests the core check_permission helper function and DRF permission classes. """

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(email="owner@example.com", username="owner", password="pw")
        cls.editor = User.objects.create_user(email="editor@example.com", username="editor", password="pw")
        cls.viewer = User.objects.create_user(email="viewer@example.com", username="viewer", password="pw")
        cls.manager = User.objects.create_user(email="manager@example.com", username="manager", password="pw")
        cls.group_member = User.objects.create_user(email="member@example.com", username="member", password="pw")
        cls.other_user = User.objects.create_user(email="other@example.com", username="other", password="pw")
        cls.admin = User.objects.create_superuser(email="admin@example.com", username="admin", password="pw")
        cls.anonymous = AnonymousUser()

        cls.page_private = Page.objects.create(name="Private Page", owner=cls.owner)
        cls.page_public = Page.objects.create(name="Public Page", owner=cls.owner)
        cls.page_group = Page.objects.create(name="Group Page", owner=cls.owner)

        cls.edit_group = Group.objects.create(name="Page Editors", owner=cls.owner)
        cls.edit_group.members.add(cls.group_member)

        # Setup Permissions
        # Private Page: owner=all, editor=edit, viewer=view, manager=manage
        PagePermission.objects.create(page=cls.page_private, level='VIEW', target_type='USER', target_user=cls.viewer)
        PagePermission.objects.create(page=cls.page_private, level='EDIT', target_type='USER', target_user=cls.editor)
        PagePermission.objects.create(page=cls.page_private, level='MANAGE', target_type='USER', target_user=cls.manager)

        # Public Page: public=view
        PagePermission.objects.create(page=cls.page_public, level='VIEW', target_type='PUBLIC')
        # Also give editor specific edit rights on public page
        PagePermission.objects.create(page=cls.page_public, level='EDIT', target_type='USER', target_user=cls.editor)


        # Group Page: group=edit
        PagePermission.objects.create(page=cls.page_group, level='EDIT', target_type='GROUP', target_group=cls.edit_group)


    # --- Test check_permission Helper ---

    def test_check_owner_permissions(self):
        """ Owner should have all permissions. """
        self.assertTrue(check_permission(self.owner, self.page_private, PagePermission.Level.VIEW))
        self.assertTrue(check_permission(self.owner, self.page_private, PagePermission.Level.EDIT))
        self.assertTrue(check_permission(self.owner, self.page_private, PagePermission.Level.MANAGE))
        self.assertTrue(check_permission(self.owner, self.page_public, PagePermission.Level.MANAGE))

    def test_check_admin_permissions(self):
        """ Admin (superuser) should have all permissions. """
        self.assertTrue(check_permission(self.admin, self.page_private, PagePermission.Level.VIEW))
        self.assertTrue(check_permission(self.admin, self.page_private, PagePermission.Level.EDIT))
        self.assertTrue(check_permission(self.admin, self.page_private, PagePermission.Level.MANAGE))

    def test_check_anonymous_permissions(self):
        """ Anonymous users should only access public view. """
        self.assertFalse(check_permission(self.anonymous, self.page_private, PagePermission.Level.VIEW))
        self.assertFalse(check_permission(self.anonymous, self.page_private, PagePermission.Level.EDIT))
        self.assertTrue(check_permission(self.anonymous, self.page_public, PagePermission.Level.VIEW))
        self.assertFalse(check_permission(self.anonymous, self.page_public, PagePermission.Level.EDIT)) # Cannot edit public
        self.assertFalse(check_permission(self.anonymous, self.page_group, PagePermission.Level.VIEW))

    def test_check_specific_user_permissions(self):
        """ Test users with specific permission levels. """
        # Viewer
        self.assertTrue(check_permission(self.viewer, self.page_private, PagePermission.Level.VIEW))
        self.assertFalse(check_permission(self.viewer, self.page_private, PagePermission.Level.EDIT))
        self.assertFalse(check_permission(self.viewer, self.page_private, PagePermission.Level.MANAGE))
        # Editor (should also have VIEW)
        self.assertTrue(check_permission(self.editor, self.page_private, PagePermission.Level.VIEW))
        self.assertTrue(check_permission(self.editor, self.page_private, PagePermission.Level.EDIT))
        self.assertFalse(check_permission(self.editor, self.page_private, PagePermission.Level.MANAGE))
         # Manager (should have VIEW and EDIT)
        self.assertTrue(check_permission(self.manager, self.page_private, PagePermission.Level.VIEW))
        self.assertTrue(check_permission(self.manager, self.page_private, PagePermission.Level.EDIT))
        self.assertTrue(check_permission(self.manager, self.page_private, PagePermission.Level.MANAGE))
        # Other user (no specific permissions on private page)
        self.assertFalse(check_permission(self.other_user, self.page_private, PagePermission.Level.VIEW))

    def test_check_group_permissions(self):
        """ Test users accessing via group permissions. """
        # Group member has EDIT on group page (implies VIEW)
        self.assertTrue(check_permission(self.group_member, self.page_group, PagePermission.Level.VIEW))
        self.assertTrue(check_permission(self.group_member, self.page_group, PagePermission.Level.EDIT))
        self.assertFalse(check_permission(self.group_member, self.page_group, PagePermission.Level.MANAGE))
        # Other user (not in group)
        self.assertFalse(check_permission(self.other_user, self.page_group, PagePermission.Level.VIEW))

    def test_check_public_permissions_authenticated(self):
         """ Test authenticated users accessing public pages. """
         # Viewer (no specific perm on public page) can view via PUBLIC
         self.assertTrue(check_permission(self.viewer, self.page_public, PagePermission.Level.VIEW))
         self.assertFalse(check_permission(self.viewer, self.page_public, PagePermission.Level.EDIT))
         # Editor (has specific EDIT perm) can edit
         self.assertTrue(check_permission(self.editor, self.page_public, PagePermission.Level.EDIT))


    # --- Test DRF Permission Classes (Optional - Requires mock request/view) ---
    # These tests are often better handled by integration tests on the actual views.
    # Example structure if testing directly:

    # def test_can_view_page_permission_class(self):
    #     from rest_framework.test import APIRequestFactory
    #     from rest_framework.views import APIView
    #     factory = APIRequestFactory()
    #     request = factory.get('/')
    #     view = APIView() # Mock view

    #     # Test viewer can view private page
    #     request.user = self.viewer
    #     permission = CanViewPage()
    #     self.assertTrue(permission.has_object_permission(request, view, self.page_private))

    #     # Test other user cannot view private page
    #     request.user = self.other_user
    #     self.assertFalse(permission.has_object_permission(request, view, self.page_private))

    #     # Test anonymous can view public page
    #     request.user = self.anonymous
    #     self.assertTrue(permission.has_object_permission(request, view, self.page_public))

    # Add similar tests for CanEditPage, CanManagePagePermissions etc.
