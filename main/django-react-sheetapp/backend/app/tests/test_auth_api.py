from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.middleware.csrf import get_token

User = get_user_model()

class AuthAPITests(APITestCase):
    """ Tests for the authentication related API endpoints (Register, Login, Logout, Status). """

    def setUp(self):
        # APITestCase automatically provides a test client
        # self.client = APIClient() # Not needed explicitly unless configuring client further
        self.register_url = reverse('auth-register')
        self.login_url = reverse('auth-login')
        self.logout_url = reverse('auth-logout')
        self.status_url = reverse('auth-status')
        self.csrf_url = reverse('auth-csrf')

        # Test user data
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword123',
            'password2': 'testpassword123',
        }
        # Create an existing user for login/logout tests
        self.existing_user = User.objects.create_user(**{k: v for k, v in self.user_data.items() if k != 'password2'})


    def _get_csrf_token(self):
        """ Helper to fetch and set CSRF token for the client. """
        response = self.client.get(self.csrf_url) # Ensure CSRF cookie is set
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        csrf_token = response.cookies.get('csrftoken')
        if csrf_token:
            self.client.credentials(HTTP_X_CSRFTOKEN=csrf_token.value)
        else:
            # Fallback or error if cookie not set as expected
            print("Warning: CSRF cookie not found after GET request.")
            # Try getting from meta (might work depending on Django/DRF version/settings)
            csrf_token_meta = get_token(response.wsgi_request)
            if csrf_token_meta:
                 self.client.credentials(HTTP_X_CSRFTOKEN=csrf_token_meta)
            else:
                 raise ValueError("Could not obtain CSRF token for testing.")


    def test_register_user_success(self):
        """ Test successful user registration. """
        new_user_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpassword123',
            'password2': 'newpassword123',
        }
        response = self.client.post(self.register_url, new_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2) # Existing user + new user
        self.assertEqual(response.data['email'], new_user_data['email'])
        self.assertEqual(response.data['username'], new_user_data['username'])
        self.assertNotIn('password', response.data) # Ensure password not returned

    def test_register_user_password_mismatch(self):
        """ Test registration failure with mismatched passwords. """
        invalid_data = self.user_data.copy()
        invalid_data['password2'] = 'wrongpassword'
        response = self.client.post(self.register_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password2', response.data) # Check specific error key

    def test_register_user_duplicate_email(self):
        """ Test registration failure with duplicate email. """
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_register_user_duplicate_username(self):
        """ Test registration failure with duplicate username. """
        dup_username_data = self.user_data.copy()
        dup_username_data['email'] = 'another@example.com' # Different email, same username
        response = self.client.post(self.register_url, dup_username_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_login_user_success(self):
        """ Test successful user login and session creation. """
        self._get_csrf_token() # Get CSRF token before POST
        login_data = {'email': self.user_data['email'], 'password': self.user_data['password']}
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user_data['email'])
        # Check if session cookie is set (APITestCase client handles cookies)
        self.assertIn('sessionid', self.client.cookies)
        # Verify auth status after login
        status_response = self.client.get(self.status_url)
        self.assertTrue(status_response.data['isAuthenticated'])
        self.assertEqual(status_response.data['user']['email'], self.user_data['email'])

    def test_login_user_invalid_password(self):
        """ Test login failure with incorrect password. """
        self._get_csrf_token()
        login_data = {'email': self.user_data['email'], 'password': 'wrongpassword'}
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertNotIn('sessionid', self.client.cookies)

    def test_login_user_nonexistent_email(self):
        """ Test login failure with non-existent email. """
        self._get_csrf_token()
        login_data = {'email': 'nouser@example.com', 'password': 'password'}
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    def test_auth_status_unauthenticated(self):
        """ Test auth status endpoint for an unauthenticated user. """
        response = self.client.get(self.status_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['isAuthenticated'])
        self.assertIsNone(response.data['user'])

    def test_logout_user_success(self):
        """ Test successful user logout and session termination. """
        self._get_csrf_token()
        # First, log in the user
        login_data = {'email': self.user_data['email'], 'password': self.user_data['password']}
        self.client.post(self.login_url, login_data, format='json')
        self.assertIn('sessionid', self.client.cookies) # Verify login worked

        # Then, attempt logout (requires CSRF token from logged-in session)
        self._get_csrf_token() # Re-fetch CSRF *after* login if it rotates
        logout_response = self.client.post(self.logout_url, {}, format='json')
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        self.assertNotIn('sessionid', self.client.cookies) # Check session cookie is cleared/invalidated

        # Verify auth status after logout
        status_response = self.client.get(self.status_url)
        self.assertFalse(status_response.data['isAuthenticated'])

    def test_logout_user_unauthenticated(self):
        """ Test logout endpoint failure for an unauthenticated user. """
        # Don't log in first
        self._get_csrf_token() # Still need CSRF for POST
        response = self.client.post(self.logout_url, {}, format='json')
        # Should fail because user is not authenticated (permission denied)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
