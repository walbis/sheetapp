from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import IntegrityError
from ..models import Page, Column, Row, Cell, Group, PagePermission, Todo, TodoStatus, Version

# Get the custom User model
User = get_user_model()

class UserModelTests(TestCase):

    def test_create_user_email_required(self):
        """ Test that creating a user without an email raises ValueError. """
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', username='test', password='password123')

    def test_create_user_successful(self):
        """ Test creating a standard user successfully. """
        email = "test@example.com"
        username = "testuser"
        password = "password123"
        user = User.objects.create_user(email=email, username=username, password=password)
        self.assertEqual(user.email, email)
        self.assertEqual(user.username, username)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password(password))
        self.assertEqual(str(user), email)

    def test_create_superuser_successful(self):
        """ Test creating a superuser successfully. """
        email = "super@example.com"
        username = "superuser"
        password = "password123"
        admin_user = User.objects.create_superuser(email=email, username=username, password=password)
        self.assertEqual(admin_user.email, email)
        self.assertEqual(admin_user.username, username)
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.check_password(password))

    def test_create_superuser_flags_required(self):
        """ Test that superuser must have is_staff and is_superuser set to True. """
        with self.assertRaises(ValueError):
            User.objects.create_superuser(email="test@example.com", username="test", password="pw", is_staff=False)
        with self.assertRaises(ValueError):
            User.objects.create_superuser(email="test@example.com", username="test", password="pw", is_superuser=False)

    def test_unique_email_constraint(self):
        """ Test that creating a user with a duplicate email raises IntegrityError. """
        email = "duplicate@example.com"
        User.objects.create_user(email=email, username="user1", password="pw")
        with self.assertRaises(IntegrityError):
            User.objects.create_user(email=email, username="user2", password="pw")

    def test_unique_username_constraint(self):
        """ Test that creating a user with a duplicate username raises IntegrityError. """
        username = "duplicateuser"
        User.objects.create_user(email="user1@example.com", username=username, password="pw")
        with self.assertRaises(IntegrityError):
            User.objects.create_user(email="user2@example.com", username=username, password="pw")


class PageModelTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email="pageowner@example.com", username="pageowner", password="pw")

    def test_page_creation_and_defaults(self):
        """ Test creating a page and that defaults (like owner, timestamps) are set. """
        page = Page.objects.create(name="My Test Page", owner=self.user)
        self.assertEqual(page.name, "My Test Page")
        self.assertEqual(page.owner, self.user)
        self.assertIsNotNone(page.created_at)
        self.assertIsNotNone(page.updated_at)
        self.assertIsNotNone(page.slug) # Slug should be generated
        self.assertEqual(page.slug, "my-test-page")
        self.assertEqual(str(page), "My Test Page")

    def test_page_slug_uniqueness(self):
        """ Test that slugs are unique, potentially with suffixes. """
        Page.objects.create(name="Duplicate Name", owner=self.user)
        page2 = Page.objects.create(name="Duplicate Name", owner=self.user)
        self.assertEqual(page2.slug, "duplicate-name-1")

    def test_setup_default_structure(self):
        """ Test the method that creates default columns for a new page. """
        page = Page.objects.create(name="Structure Test", owner=self.user)
        self.assertEqual(page.columns.count(), 0) # No columns initially
        page.setup_default_structure()
        self.assertEqual(page.columns.count(), 2)
        col_a = page.columns.get(order=1)
        col_b = page.columns.get(order=2)
        self.assertEqual(col_a.name, "Column A")
        self.assertEqual(col_b.name, "Column B")
        self.assertEqual(col_a.width, 150)


class StructureModelTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email="structowner@example.com", username="structowner", password="pw")
        cls.page = Page.objects.create(name="Structure Page", owner=cls.user)

    def test_column_creation(self):
        """ Test creating a Column associated with a Page. """
        column = Column.objects.create(page=self.page, name="Test Col", order=1, width=200)
        self.assertEqual(column.page, self.page)
        self.assertEqual(column.name, "Test Col")
        self.assertEqual(column.order, 1)
        self.assertEqual(column.width, 200)
        self.assertEqual(str(column), "Page 'Structure Page' - Col 1: Test Col")

    def test_row_creation(self):
        """ Test creating a Row associated with a Page. """
        row = Row.objects.create(page=self.page, order=1)
        self.assertEqual(row.page, self.page)
        self.assertEqual(row.order, 1)
        self.assertEqual(str(row), "Page 'Structure Page' - Row 1")

    def test_column_order_uniqueness(self):
        """ Test unique_together constraint for (page, column order). """
        Column.objects.create(page=self.page, name="Col1", order=1)
        with self.assertRaises(IntegrityError):
            Column.objects.create(page=self.page, name="Col1 Dupe", order=1)

    def test_row_order_uniqueness(self):
        """ Test unique_together constraint for (page, row order). """
        Row.objects.create(page=self.page, order=1)
        with self.assertRaises(IntegrityError):
            Row.objects.create(page=self.page, order=1)


class DataModelTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email="dataowner@example.com", username="dataowner", password="pw")
        cls.page = Page.objects.create(name="Data Page", owner=cls.user)
        cls.col1 = Column.objects.create(page=cls.page, name="Col A", order=1)
        cls.col2 = Column.objects.create(page=cls.page, name="Col B", order=2)
        cls.row1 = Row.objects.create(page=cls.page, order=1)
        cls.row2 = Row.objects.create(page=cls.page, order=2)

    def test_cell_creation(self):
        """ Test creating a Cell associated with a Row and Column. """
        cell = Cell.objects.create(row=self.row1, column=self.col1, value="R1C1 Value")
        self.assertEqual(cell.row, self.row1)
        self.assertEqual(cell.column, self.col1)
        self.assertEqual(cell.value, "R1C1 Value")
        self.assertIsNotNone(cell.updated_at)
        # Test string representation (adjust based on actual implementation)
        self.assertIn("Cell(R1, C1): 'R1C1 Value'", str(cell))

    def test_cell_unique_together(self):
        """ Test unique_together constraint for (row, column). """
        Cell.objects.create(row=self.row1, column=self.col1, value="First")
        with self.assertRaises(IntegrityError):
            Cell.objects.create(row=self.row1, column=self.col1, value="Second")

    def test_cell_blank_value(self):
        """ Test that a cell can be created with a blank value. """
        cell = Cell.objects.create(row=self.row1, column=self.col2, value="")
        self.assertEqual(cell.value, "")

    def test_cell_default_value(self):
        """ Test that a cell gets an empty string default value. """
        cell = Cell.objects.create(row=self.row2, column=self.col1) # No value provided
        self.assertEqual(cell.value, "")


class PermissionModelTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(email="permissowner@example.com", username="permissowner", password="pw")
        cls.user1 = User.objects.create_user(email="user1@example.com", username="user1", password="pw")
        cls.user2 = User.objects.create_user(email="user2@example.com", username="user2", password="pw")
        cls.page = Page.objects.create(name="Permiss Page", owner=cls.owner)
        cls.group = Group.objects.create(name="Editors", owner=cls.owner)
        cls.group.members.add(cls.user1) # Add user1 to group

    def test_group_creation(self):
        self.assertEqual(self.group.name, "Editors")
        self.assertEqual(self.group.owner, self.owner)
        self.assertIn(self.user1, self.group.members.all())
        self.assertNotIn(self.user2, self.group.members.all())
        self.assertEqual(str(self.group), "Editors")

    def test_page_permission_creation_user(self):
        """ Test creating a user-specific permission. """
        perm = PagePermission.objects.create(
            page=self.page,
            level=PagePermission.Level.EDIT,
            target_type=PagePermission.TargetType.USER,
            target_user=self.user1,
            granted_by=self.owner
        )
        self.assertEqual(perm.page, self.page)
        self.assertEqual(perm.level, 'EDIT')
        self.assertEqual(perm.target_type, 'USER')
        self.assertEqual(perm.target_user, self.user1)
        self.assertIsNone(perm.target_group)
        self.assertIn(self.user1.email, str(perm))

    def test_page_permission_creation_group(self):
        """ Test creating a group-specific permission. """
        perm = PagePermission.objects.create(
            page=self.page,
            level=PagePermission.Level.VIEW,
            target_type=PagePermission.TargetType.GROUP,
            target_group=self.group,
            granted_by=self.owner
        )
        self.assertEqual(perm.target_type, 'GROUP')
        self.assertEqual(perm.target_group, self.group)
        self.assertIsNone(perm.target_user)
        self.assertIn(self.group.name, str(perm))

    def test_page_permission_creation_public(self):
        """ Test creating a public permission. """
        perm = PagePermission.objects.create(
            page=self.page,
            level=PagePermission.Level.VIEW,
            target_type=PagePermission.TargetType.PUBLIC,
            granted_by=self.owner
        )
        self.assertEqual(perm.target_type, 'PUBLIC')
        self.assertIsNone(perm.target_group)
        self.assertIsNone(perm.target_user)
        self.assertIn("Public", str(perm))

    def test_page_permission_validation_constraints(self):
        """ Test validation logic in PagePermission.clean() or DB constraints. """
        # User type requires user
        with self.assertRaises(ValidationError):
            PagePermission(page=self.page, level='VIEW', target_type='USER', target_group=self.group).clean()
        # Group type requires group
        with self.assertRaises(ValidationError):
             PagePermission(page=self.page, level='VIEW', target_type='GROUP', target_user=self.user1).clean()
        # Public type cannot have user/group and must be VIEW
        with self.assertRaises(ValidationError):
            PagePermission(page=self.page, level='VIEW', target_type='PUBLIC', target_user=self.user1).clean()
        with self.assertRaises(ValidationError):
            PagePermission(page=self.page, level='EDIT', target_type='PUBLIC').clean()

    def test_page_permission_uniqueness(self):
        """ Test unique_together constraint. """
        PagePermission.objects.create(page=self.page, level='VIEW', target_type='USER', target_user=self.user1)
        with self.assertRaises(IntegrityError):
             PagePermission.objects.create(page=self.page, level='VIEW', target_type='USER', target_user=self.user1)


class TodoModelTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.creator = User.objects.create_user(email="todo_creator@example.com", username="todocreator", password="pw")
        cls.page = Page.objects.create(name="Todo Source Page", owner=cls.creator)
        cls.row1 = Row.objects.create(page=cls.page, order=1)
        cls.row2 = Row.objects.create(page=cls.page, order=2)

    def test_todo_creation_and_defaults(self):
        """ Test creating a ToDo list and default values. """
        todo = Todo.objects.create(name="My Tasks", source_page=self.page, creator=self.creator)
        self.assertEqual(todo.name, "My Tasks")
        self.assertEqual(todo.source_page, self.page)
        self.assertEqual(todo.creator, self.creator)
        self.assertTrue(todo.is_personal) # Default
        self.assertIsNotNone(todo.slug)
        self.assertEqual(todo.slug, "my-tasks")
        self.assertIn("Personal", str(todo))
        self.assertIn(self.page.name, str(todo))

    def test_todo_slug_uniqueness_per_page(self):
        """ Test that ToDo slugs are unique within the context of a source page. """
        Todo.objects.create(name="My Tasks", source_page=self.page, creator=self.creator)
        todo2 = Todo.objects.create(name="My Tasks", source_page=self.page, creator=self.creator)
        self.assertEqual(todo2.slug, "my-tasks-1")

        # Create another page and check slug can be reused there
        page2 = Page.objects.create(name="Another Page", owner=self.creator)
        todo3 = Todo.objects.create(name="My Tasks", source_page=page2, creator=self.creator)
        self.assertEqual(todo3.slug, "my-tasks") # Should be allowed on different page

    def test_initialize_statuses(self):
        """ Test that initial statuses are created for source page rows. """
        todo = Todo.objects.create(name="Status Test", source_page=self.page, creator=self.creator)
        self.assertEqual(todo.statuses.count(), 0) # No statuses initially
        todo.initialize_statuses()
        self.assertEqual(todo.statuses.count(), 2) # Should match number of rows in source page
        status1 = todo.statuses.get(row=self.row1)
        status2 = todo.statuses.get(row=self.row2)
        self.assertEqual(status1.status, TodoStatus.Status.NOT_STARTED)
        self.assertEqual(status2.status, TodoStatus.Status.NOT_STARTED)
        self.assertEqual(status1.row, self.row1)
        self.assertEqual(status2.row, self.row2)

    def test_todo_status_creation(self):
        """ Test creating a specific TodoStatus entry. """
        todo = Todo.objects.create(name="Status Create", source_page=self.page, creator=self.creator)
        status = TodoStatus.objects.create(todo=todo, row=self.row1, status=TodoStatus.Status.IN_PROGRESS)
        self.assertEqual(status.todo, todo)
        self.assertEqual(status.row, self.row1)
        self.assertEqual(status.status, TodoStatus.Status.IN_PROGRESS)
        self.assertIn(TodoStatus.Status.IN_PROGRESS.label, str(status))

    def test_todo_status_uniqueness(self):
        """ Test unique_together constraint for (todo, row). """
        todo = Todo.objects.create(name="Status Unique", source_page=self.page, creator=self.creator)
        TodoStatus.objects.create(todo=todo, row=self.row1)
        with self.assertRaises(IntegrityError):
            TodoStatus.objects.create(todo=todo, row=self.row1)

    def test_todo_status_row_page_validation(self):
        """ Test that TodoStatus row must belong to the Todo's source page. """
        todo = Todo.objects.create(name="Status Validate", source_page=self.page, creator=self.creator)
        other_page = Page.objects.create(name="Other Page", owner=self.creator)
        other_row = Row.objects.create(page=other_page, order=1)
        with self.assertRaises(ValidationError):
            # Attempt to create status linking todo to a row from a different page
            status = TodoStatus(todo=todo, row=other_row, status=TodoStatus.Status.COMPLETED)
            status.clean() # Manually call clean to trigger validation

# Add tests for Version model if needed (usually tested via PageSaveView tests)
