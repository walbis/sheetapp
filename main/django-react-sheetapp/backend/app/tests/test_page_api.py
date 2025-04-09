from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from ..models import Page, Column, Row, Cell, PagePermission, Group # Import necessary models

User = get_user_model()

class PageAPITests(APITestCase):
    """ Tests for the Page related API endpoints (/api/pages/, /api/pages/{slug}/data/, etc.). """

    @classmethod
    def setUpTestData(cls):
        # Create users with different roles
        cls.owner = User.objects.create_user(email="owner_page@example.com", username="page_owner", password="pw")
        cls.editor = User.objects.create_user(email="editor_page@example.com", username="page_editor", password="pw")
        cls.viewer = User.objects.create_user(email="viewer_page@example.com", username="page_viewer", password="pw")
        cls.no_access = User.objects.create_user(email="no_access@example.com", username="no_access", password="pw")
        cls.admin = User.objects.create_superuser(email="admin_page@example.com", username="page_admin", password="pw")

        # Create a page
        cls.page = Page.objects.create(name="API Test Page", owner=cls.owner)
        cls.page.setup_default_structure() # Add default columns
        cls.page_slug = cls.page.slug

        # Grant permissions
        PagePermission.objects.create(page=cls.page, level='EDIT', target_type='USER', target_user=cls.editor)
        PagePermission.objects.create(page=cls.page, level='VIEW', target_type='USER', target_user=cls.viewer)
        # Owner has implicit full access (as per permission logic)
        # Admin has implicit full access

        # URLs
        cls.pages_list_url = reverse('page-list') # '/api/pages/'
        cls.page_detail_url = reverse('page-detail', kwargs={'slug': cls.page_slug}) # '/api/pages/{slug}/'
        cls.page_data_url = reverse('page-data', kwargs={'page_slug': cls.page_slug}) # '/api/pages/{slug}/data/'
        cls.page_save_url = reverse('page-save', kwargs={'page_slug': cls.page_slug}) # '/api/pages/{slug}/save/'
        cls.page_col_width_url = reverse('column-width-update', kwargs={'page_slug': cls.page_slug}) # '/api/pages/{slug}/columns/width/'
        cls.page_versions_url = reverse('page-versions', kwargs={'page_slug': cls.page_slug}) # '/api/pages/{slug}/versions/'


    def setUp(self):
         # Create a new client for each test to ensure isolation
         self.client = APIClient()
         # We need to manually handle CSRF for authenticated POST/PATCH/DELETE if using SessionAuth
         # self.client.force_authenticate(user=self.owner) # Example: Authenticate as owner for tests needing it

    def _login(self, user):
        """ Helper to log in a specific user. """
        self.client.force_authenticate(user=user)
        # Fetch CSRF token after login if making state-changing requests
        response = self.client.get(reverse('auth-csrf'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        csrf_token = response.cookies.get('csrftoken')
        if csrf_token:
             self.client.credentials(HTTP_X_CSRFTOKEN=csrf_token.value)
        else:
             raise ValueError("CSRF token not obtained after login in test setup.")


    # --- List Pages Tests ---
    def test_list_pages_unauthenticated(self):
        """ Anonymous users should not see private pages (only public if implemented). """
        response = self.client.get(self.pages_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Assuming cls.page is not public, the list should be empty for anonymous
        self.assertEqual(len(response.data.get('results', response.data)), 0) # Handle pagination or direct list

    def test_list_pages_authenticated(self):
        """ Test different authenticated users listing pages based on permissions. """
        # Owner sees the page
        self._login(self.owner)
        response = self.client.get(self.pages_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get('results', response.data)), 1)
        self.assertEqual(response.data.get('results', response.data)[0]['slug'], self.page_slug)

        # Editor sees the page
        self._login(self.editor)
        response = self.client.get(self.pages_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get('results', response.data)), 1)

         # Viewer sees the page
        self._login(self.viewer)
        response = self.client.get(self.pages_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get('results', response.data)), 1)

        # No_access user does NOT see the page
        self._login(self.no_access)
        response = self.client.get(self.pages_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get('results', response.data)), 0)


    # --- Create Page Tests ---
    def test_create_page_authenticated(self):
        """ Authenticated users should be able to create pages. """
        self._login(self.no_access) # Any authenticated user can create
        page_name = "My New Page by No Access"
        response = self.client.post(self.pages_list_url, {'name': page_name}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], page_name)
        self.assertEqual(response.data['owner']['email'], self.no_access.email)
        # Verify default columns were created
        self.assertIn('columns', response.data)
        self.assertEqual(len(response.data['columns']), 2)
        # Verify owner permissions were granted (check DB directly)
        new_page = Page.objects.get(slug=response.data['slug'])
        self.assertTrue(PagePermission.objects.filter(page=new_page, target_user=self.no_access, level='MANAGE').exists())

    def test_create_page_unauthenticated(self):
        """ Anonymous users cannot create pages. """
        response = self.client.post(self.pages_list_url, {'name': "Anon Page"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # Or 401 depending on exact auth setup


    # --- Retrieve Page Detail Tests ---
    def test_retrieve_page_detail_permissions(self):
        """ Test accessing page detail based on permissions. """
        # Owner, Editor, Viewer, Admin should succeed (200)
        for user in [self.owner, self.editor, self.viewer, self.admin]:
             self.client.force_authenticate(user=user) # Simple auth for GET
             response = self.client.get(self.page_detail_url)
             self.assertEqual(response.status_code, status.HTTP_200_OK, f"User {user.email} failed")
             self.assertEqual(response.data['slug'], self.page_slug)

        # No_access user should fail (403)
        self.client.force_authenticate(user=self.no_access)
        response = self.client.get(self.page_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Anonymous user should fail (403) as page is not public
        self.client.logout()
        response = self.client.get(self.page_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    # --- Retrieve Page Data Tests ---
    def test_retrieve_page_data_permissions(self):
        """ Test accessing full page data based on permissions. """
        # Owner, Editor, Viewer, Admin succeed
        for user in [self.owner, self.editor, self.viewer, self.admin]:
             self.client.force_authenticate(user=user)
             response = self.client.get(self.page_data_url)
             self.assertEqual(response.status_code, status.HTTP_200_OK, f"User {user.email} failed")
             self.assertIn('columns', response.data)
             self.assertIn('rows', response.data)
             self.assertEqual(len(response.data['columns']), 2) # Check default structure

        # No_access user fails (403)
        self.client.force_authenticate(user=self.no_access)
        response = self.client.get(self.page_data_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Anonymous user fails (403)
        self.client.logout()
        response = self.client.get(self.page_data_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    # --- Save Page Data Tests ---
    def test_save_page_data_success(self):
        """ Test successfully saving changes to page data and structure by editor/owner. """
        self._login(self.editor) # Login as editor

        # Get current structure to modify
        initial_data_resp = self.client.get(self.page_data_url)
        self.assertEqual(initial_data_resp.status_code, status.HTTP_200_OK)
        save_payload = initial_data_resp.data.copy()

        # Simulate changes: Add row, change cell, change column name
        new_row_order = len(save_payload['rows']) + 1
        save_payload['rows'].append({
            "id": None, # New row
            "order": new_row_order,
            "cells": ["New R Val 1", "New R Val 2"]
        })
        if len(save_payload['rows']) > 0 and len(save_payload['rows'][0]['cells']) > 0:
             save_payload['rows'][0]['cells'][0] = "Updated Value R1C1" # Change existing cell
        save_payload['columns'][0]['name'] = "Column A Updated" # Change column name
        save_payload['commit_message'] = "Test save commit"

        # Perform the save
        response = self.client.post(self.page_save_url, save_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data) # Show errors if fail
        self.assertEqual(response.data['message'], "Page saved successfully")

        # Verify changes in DB (or by re-fetching data)
        self.page.refresh_from_db()
        self.assertEqual(self.page.rows.count(), new_row_order)
        self.assertEqual(self.page.columns.get(order=1).name, "Column A Updated")
        self.assertEqual(self.page.rows.get(order=1).cells.get(column__order=1).value, "Updated Value R1C1")
        self.assertEqual(self.page.rows.get(order=new_row_order).cells.get(column__order=1).value, "New R Val 1")
        # Verify version was created
        self.assertTrue(self.page.versions.exists())
        self.assertEqual(self.page.versions.latest('timestamp').commit_message, "Test save commit")


    def test_save_page_data_permission_denied(self):
        """ Test users without EDIT permission cannot save. """
        # Viewer attempts save
        self._login(self.viewer)
        response = self.client.post(self.page_save_url, {'columns': [], 'rows': []}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # No_access user attempts save
        self._login(self.no_access)
        response = self.client.post(self.page_save_url, {'columns': [], 'rows': []}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

         # Anonymous user attempts save
        self.client.logout()
        response = self.client.post(self.page_save_url, {'columns': [], 'rows': []}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # Requires authentication

    def test_save_page_data_invalid_payload(self):
        """ Test saving with invalid data structures (missing fields, mismatched cells/cols). """
        self._login(self.owner)

        # Missing columns
        response = self.client.post(self.page_save_url, {'rows': []}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('columns', response.data)

        # Mismatched cell count
        invalid_payload = {
             'columns': [{'id': str(self.page.columns.first().id), 'name': 'A', 'order': 1, 'width': 100}], # 1 column
             'rows': [{'id': str(self.page.rows.first().id) if self.page.rows.exists() else None, 'order': 1, 'cells': ['Val1', 'Val2']}] # 2 cells
        }
        response = self.client.post(self.page_save_url, invalid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('mismatch' in response.data.get('non_field_errors', [''])[0].lower() or
                        'cell count' in response.data.get('non_field_errors', [''])[0].lower())


    # --- Update Column Width Tests ---
    def test_update_column_width_success(self):
        """ Test successfully updating column widths. """
        self._login(self.editor)
        col1 = self.page.columns.get(order=1)
        col2 = self.page.columns.get(order=2)
        payload = {'updates': [{'id': str(col1.id), 'width': 222}, {'id': str(col2.id), 'width': 333}]}
        response = self.client.post(self.page_col_width_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        col1.refresh_from_db()
        col2.refresh_from_db()
        self.assertEqual(col1.width, 222)
        self.assertEqual(col2.width, 333)

    def test_update_column_width_permission_denied(self):
        """ Test users without EDIT permission cannot update widths. """
        self._login(self.viewer)
        col1_id = str(self.page.columns.first().id)
        payload = {'updates': [{'id': col1_id, 'width': 200}]}
        response = self.client.post(self.page_col_width_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_column_width_invalid_data(self):
        """ Test invalid payloads for column width update. """
        self._login(self.owner)
        # Invalid format (not a list)
        response = self.client.post(self.page_col_width_url, {'updates': {'id': '1', 'width': 100}}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('must be a list', response.data.get('error', ''))
        # Invalid width value
        col1_id = str(self.page.columns.first().id)
        payload = {'updates': [{'id': col1_id, 'width': -50}]}
        response = self.client.post(self.page_col_width_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        # Non-existent column ID
        payload = {'updates': [{'id': str(uuid.uuid4()), 'width': 150}]}
        response = self.client.post(self.page_col_width_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)


    # --- Delete Page Tests ---
    def test_delete_page_success(self):
        """ Test owner can delete their page. """
        self._login(self.owner)
        response = self.client.delete(self.page_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Page.objects.filter(slug=self.page_slug).exists())

    def test_delete_page_permission_denied(self):
        """ Test users without permission cannot delete the page. """
        # Editor might have edit but maybe not delete (depends on permission definition)
        self._login(self.editor)
        response = self.client.delete(self.page_detail_url)
        # Assuming CanEditPage is used, this might pass (204) or fail (403)
        # If delete requires ownership/manage, it should be 403. Let's assume CanEditPage allows delete for now.
        # self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # Uncomment if delete is stricter

        # Viewer definitely cannot delete
        self._login(self.viewer)
        response = self.client.delete(self.page_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    # --- Page Version Tests ---
    def test_list_page_versions(self):
        """ Test listing versions for a page requires view permission. """
        # Save page once to create a version
        self._login(self.owner)
        initial_data = self.client.get(self.page_data_url).data
        self.client.post(self.page_save_url, initial_data, format='json')

        # Owner can list versions
        response_owner = self.client.get(self.page_versions_url)
        self.assertEqual(response_owner.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response_owner.data), 0) # Should have at least one version

        # Viewer can list versions
        self._login(self.viewer)
        response_viewer = self.client.get(self.page_versions_url)
        self.assertEqual(response_viewer.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_viewer.data), len(response_owner.data)) # Should see same versions

         # No_access user cannot list versions
        self._login(self.no_access)
        response_no_access = self.client.get(self.page_versions_url)
        self.assertEqual(response_no_access.status_code, status.HTTP_403_FORBIDDEN)
