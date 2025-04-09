import logging
from rest_framework import generics, status, permissions, views
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
# Use relative imports within the app
from ..serializers import UserSerializer, RegisterSerializer, LoginSerializer
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect, csrf_exempt

# Get the logger instance configured in settings.py
logger = logging.getLogger(__name__)

class CsrfTokenView(views.APIView):
    """
    A simple view to ensure the CSRF cookie is set for the frontend.
    The frontend JavaScript needs this cookie to be present to read the token value
    and include it in the 'X-CSRFToken' header for POST/PUT/PATCH/DELETE requests.
    """
    permission_classes = [permissions.AllowAny] # Accessible by anyone

    @method_decorator(ensure_csrf_cookie) # Decorator that sets the CSRF cookie on the response
    def get(self, request, *args, **kwargs):
        # The main purpose is served by the decorator setting the cookie.
        # Optionally, we can return the token value in the response body if needed.
        csrf_token = get_token(request)
        logger.debug(f"CSRF cookie set via CsrfTokenView. Token value: {csrf_token}") # Log token for debug
        return Response({'message': 'CSRF cookie set.'})


class RegisterView(generics.CreateAPIView):
    """ API endpoint for new user registration. """
    serializer_class = RegisterSerializer # Use the serializer defined for registration
    permission_classes = [permissions.AllowAny] # Allow any user (authenticated or not) to register

    # No CSRF protection needed for registration itself typically,
    # as it doesn't rely on an existing authenticated session.
    def create(self, request, *args, **kwargs):
        """ Handles POST request for user registration. """
        logger.info(f"Registration attempt received for email: {request.data.get('email')}")
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True) # Validate input data, raise error if invalid
            user = serializer.save() # Serializer's create() method handles user creation and password hashing
            logger.info(f"User '{user.email}' registered successfully.")
            # Return the newly created user's data (excluding sensitive info like password)
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        except serializers.ValidationError:
            # Log validation errors (already logged by DRF default handler potentially)
            logger.warning(f"Registration validation failed: {serializer.errors}")
            # is_valid(raise_exception=True) automatically returns 400 response with errors
            # This block is technically redundant if raise_exception=True, but kept for clarity
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Catch unexpected errors during the save process
            logger.error(f"Unexpected error during user registration save: {e}", exc_info=True)
            return Response({"error": "Registration failed due to an server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoginView(generics.GenericAPIView):
    """ API endpoint for user login using email and password. """
    serializer_class = LoginSerializer # Use the serializer defined for login input validation
    permission_classes = [permissions.AllowAny] # Allow anyone to attempt login

    # Apply CSRF protection decorator to the post method
    # This ensures the request includes a valid CSRF token (obtained via CsrfTokenView)
    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        """ Handles POST request for user login. """
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True) # Validate email/password format
        except serializers.ValidationError:
            logger.warning(f"Login validation failed for input: {request.data.get('email')}, Errors: {serializer.errors}")
            return Response({"error": "Invalid input provided."}, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        logger.info(f"Login attempt for user: {email}")

        # Use Django's authentication backend
        # Pass 'request' to authenticate for session/CSRF context if needed by backends
        # Use 'username=email' because our custom User model uses email as USERNAME_FIELD
        user = authenticate(request=request, username=email, password=password)

        if user is not None:
            # Check if the user account is active
            if user.is_active:
                # Log the user in, creating a session
                login(request, user)
                logger.info(f"User '{email}' logged in successfully.")
                # Return the logged-in user's data
                return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
            else:
                # User account is disabled
                logger.warning(f"Login failed for '{email}': Account is disabled.")
                return Response({"error": "This account has been disabled."}, status=status.HTTP_403_FORBIDDEN)
        else:
            # Authentication failed (invalid email or password)
            logger.warning(f"Login failed for '{email}': Invalid credentials.")
            # Return a generic error message for security (don't reveal which part was wrong)
            return Response({"error": "Unable to log in with provided credentials."}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(views.APIView):
    """ API endpoint for user logout. """
    permission_classes = [permissions.IsAuthenticated] # User must be logged in to log out

    # Apply CSRF protection decorator to the post method
    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        """ Handles POST request for user logout. """
        user_email = request.user.email if request.user else "Unknown User"
        logger.info(f"Logout attempt for user: {user_email}")
        try:
            # Use Django's logout function to clear the session
            logout(request)
            logger.info(f"User '{user_email}' logged out successfully.")
            # Return a success response
            response = Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
            # Optionally delete other cookies if your app uses them
            # response.delete_cookie('some_other_cookie_name')
            return response
        except Exception as e:
             # Log errors during logout but still attempt to signal success to client
             logger.error(f"Error during logout for {user_email}: {e}", exc_info=True)
             # Client state should be cleared regardless of server-side session clearing success
             return Response({"message": "Logout processed, potential server error occurred."}, status=status.HTTP_200_OK)


class AuthStatusView(views.APIView):
    """
    API endpoint to check the current authentication status of the user making the request.
    Relies on the session cookie being sent with the request.
    """
    permission_classes = [permissions.AllowAny] # Allow anyone to check status

    def get(self, request, *args, **kwargs):
        """ Handles GET request to check authentication status. """
        if request.user and request.user.is_authenticated:
            # User is logged in
            logger.debug(f"Auth status check: User IS authenticated ({request.user.email})")
            # Return authenticated status and basic user info
            return Response({
                'isAuthenticated': True,
                'user': UserSerializer(request.user).data # Use UserSerializer for consistency
            }, status=status.HTTP_200_OK)
        else:
            # User is not logged in (anonymous)
            logger.debug("Auth status check: User is NOT authenticated")
            # Return not authenticated status
            return Response({'isAuthenticated': False, 'user': None}, status=status.HTTP_200_OK)

# Future: Add views for password reset request, password reset confirmation, email verification, etc.
