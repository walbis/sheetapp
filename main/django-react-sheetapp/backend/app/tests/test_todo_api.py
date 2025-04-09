from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from ..models import Page, Column, Row, Cell, Todo, TodoStatus, PagePermission # Import necessary models
import uuid # For checking UUID format if needed

User = get_user_model()

class TodoAPITests(APITestCase):
    """ Tests for the ToDo related API endpoints (/api/todos/, /api/todos/{pk}/status/{row_id}/). """

    @classmethod
    def setUpTestData(cls):
        # Create users
        cls.creator = User.objects.create_user(email="creator_todo@example.com", username="todo_creator", password="pw")
        cls.viewer = User.objects.create_user(email="viewer_todo@example.com", username="todo_viewer", password="pw")
        cls.no_access = User.objects.create_user(email="no_access_todo@example.com", username="todo_no_access", password="pw")
        cls.admin = User.objects.create_superuser(email="admin_todo@example.com", username="todo_admin", password="pw")

        # Create source page and structure
        cls.source_page = Page.objects.create(name="Todo Source Page", owner=cls.creator)
        cls.col1 = Column.objects.create(page=cls.source_page, name="Task", order=1)
        cls.row1 = Row.objects.create(page=cls.source_page, order=1)
        cls.row2 = Row.objects.create(page=cls.source_page, order=2)
        Cell.objects.create(row=cls.row1, column=cls.col1, value="Task 1")
        Cell.objects.create(row=cls.row2, column=cls.col1, value="Task 2")

        # Grant viewer permission on source page
        PagePermission.objects.create(page=cls.source_page, level='VIEW', target_type='USER', target_user=cls.viewer)

        # Create a personal ToDo by creator
        cls.personal_todo = Todo.objects.create(name="Creator Personal", source_page=cls.source_page, creator=cls.creator, is_personal=True)
        cls.personal_todo.initialize_statuses() # Create initial statuses

        # Create a non-personal ToDo by creator
        cls.public_todo = Todo.objects.create(name="Creator Public", source_page=cls.source_page, creator=cls.creator, is_personal=False)
        cls.public_todo.initialize_statuses()

        # URLs
        cls.todos_list_url = reverse('todo-list') # '/api/todos/'
        cls.personal_todo_detail_url = reverse('todo-detail', kwargs={'pk': cls.personal_todo.pk})
        cls.public_todo_detail_url = reverse('todo-detail', kwargs={'pk': cls.public_todo.pk})
        # Construct status update URL (need row ID)
        cls.status_update_url_template = f"/api/todos/{cls.public_todo.pk}/status/{cls.row1.pk}/" # Example for public todo, row 1


    def setUp(self):
         self.client = APIClient()
         # Helper to log in and get CSRF if needed (PATCH needs CSRF)
    def _login(self, user):
        self.client.force_authenticate(user=user)
        response = self.client.get(reverse('auth-csrf'))
        csrf_token = response.cookies.get('csrftoken')
        if csrf_token:
             self.client.credentials(HTTP_X_CSRFTOKEN=csrf_token.value)
        else:
             raise ValueError("CSRF token not obtained after login in ToDo test setup.")


    # --- List ToDos Tests ---
    def test_list_todos_unauthenticated(self):
        """ Anonymous users should see no ToDos. """
        response = self.client.get(self.todos_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # Requires authentication

    def test_list_todos_creator(self):
        """ Creator sees both personal and non-personal ToDos they created. """
        self._login(self.creator)
        response = self.client.get(self.todos_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 2)
        todo_ids = {str(t['id']) for t in results}
        self.assertIn(str(self.personal_todo.id), todo_ids)
        self.assertIn(str(self.public_todo.id), todo_ids)

    def test_list_todos_viewer(self):
        """ Viewer sees only non-personal ToDos for pages they can view. """
        self._login(self.viewer)
        response = self.client.get(self.todos_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1) # Only the public one
        self.assertEqual(str(results[0]['id']), str(self.public_todo.id))

    def test_list_todos_no_access(self):
        """ User with no access to source page sees no ToDos (unless they created one). """
        # Create a todo for this user on the same page (they shouldn't see public_todo)
        no_access_todo = Todo.objects.create(name="No Access Personal", source_page=self.source_page, creator=self.no_access, is_personal=True)
        self._login(self.no_access)
        response = self.client.get(self.todos_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1) # Only their own personal one
        self.assertEqual(str(results[0]['id']), str(no_access_todo.id))


    # --- Create ToDo Tests ---
    def test_create_todo_success(self):
        """ Test successfully creating a new ToDo list. """
        self._login(self.viewer) # Viewer can create ToDo as they can view source page
        payload = {
            'name': 'Viewer Todo',
            'is_personal': False,
            'source_page_slug': self.source_page.slug
        }
        response = self.client.post(self.todos_list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Viewer Todo')
        self.assertEqual(response.data['creator']['email'], self.viewer.email)
        self.assertFalse(response.data['is_personal'])
        # Verify statuses were initialized
        new_todo = Todo.objects.get(id=response.data['id'])
        self.assertEqual(new_todo.statuses.count(), self.source_page.rows.count()) # Should match row count

    def test_create_todo_no_view_permission(self):
        """ Test creating ToDo fails if user cannot view source page. """
        self._login(self.no_access)
        payload = {'name': 'Failed Todo', 'source_page_slug': self.source_page.slug}
        response = self.client.post(self.todos_list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST) # Validation error in serializer
        self.assertIn('source_page_slug', response.data) # Check error is related to slug validation

    def test_create_todo_invalid_page_slug(self):
        """ Test creating ToDo fails with non-existent source page slug. """
        self._login(self.creator)
        payload = {'name': 'Invalid Page Todo', 'source_page_slug': 'non-existent-slug'}
        response = self.client.post(self.todos_list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('source_page_slug', response.data)


    # --- Retrieve ToDo Detail Tests ---
    def test_retrieve_todo_detail_permissions(self):
        """ Test retrieving ToDo details based on user permissions. """
        # Creator can view both
        self._login(self.creator)
        res_pers = self.client.get(self.personal_todo_detail_url)
        res_pub = self.client.get(self.public_todo_detail_url)
        self.assertEqual(res_pers.status_code, status.HTTP_200_OK)
        self.assertEqual(res_pub.status_code, status.HTTP_200_OK)
        self.assertEqual(res_pers.data['id'], str(self.personal_todo.id))
        self.assertIn('statuses', res_pers.data) # Check statuses are included

        # Viewer can view public, but not personal
        self._login(self.viewer)
        res_pers_viewer = self.client.get(self.personal_todo_detail_url)
        res_pub_viewer = self.client.get(self.public_todo_detail_url)
        self.assertEqual(res_pers_viewer.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(res_pub_viewer.status_code, status.HTTP_200_OK)

        # No_access user cannot view either (they didn't create them, can't view source page for public one)
        self._login(self.no_access)
        res_pers_no = self.client.get(self.personal_todo_detail_url)
        res_pub_no = self.client.get(self.public_todo_detail_url)
        self.assertEqual(res_pers_no.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(res_pub_no.status_code, status.HTTP_403_FORBIDDEN)


    # --- Update ToDo Status Tests ---
    def test_update_todo_status_success(self):
        """ Test creator can update status on their ToDo. """
        self._login(self.creator)
        url = f"/api/todos/{self.public_todo.pk}/status/{self.row1.pk}/" # Update row1 status
        payload = {'status': 'IN_PROGRESS'}
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'IN_PROGRESS')
        # Verify in DB
        status_entry = TodoStatus.objects.get(todo=self.public_todo, row=self.row1)
        self.assertEqual(status_entry.status, 'IN_PROGRESS')

    def test_update_todo_status_permission_denied(self):
        """ Test user without permission cannot update status. """
        self._login(self.viewer) # Viewer can see public_todo but not edit status (based on IsCreatorOrAdminTodo)
        url = f"/api/todos/{self.public_todo.pk}/status/{self.row1.pk}/"
        payload = {'status': 'COMPLETED'}
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_todo_status_invalid_status(self):
        """ Test providing an invalid status value fails. """
        self._login(self.creator)
        url = f"/api/todos/{self.public_todo.pk}/status/{self.row1.pk}/"
        payload = {'status': 'INVALID_STATUS'}
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('status', response.data)

    def test_update_todo_status_invalid_row(self):
        """ Test updating status for a row not belonging to the source page fails. """
        self._login(self.creator)
        invalid_row_id = uuid.uuid4() # Non-existent row ID
        url = f"/api/todos/{self.public_todo.pk}/status/{invalid_row_id}/"
        payload = {'status': 'COMPLETED'}
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    # --- Delete ToDo Tests ---
    def test_delete_todo_success(self):
        """ Test creator can delete their ToDo. """
        self._login(self.creator)
        response = self.client.delete(self.personal_todo_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Todo.objects.filter(id=self.personal_todo.id).exists())

    def test_delete_todo_permission_denied(self):
        """ Test user without permission cannot delete ToDo. """
        self._login(self.viewer)
        response = self.client.delete(self.public_todo_detail_url) # Viewer cannot delete this
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
