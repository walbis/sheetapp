import logging
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError


logger = logging.getLogger(__name__)
User = get_user_model()

class UserBasicSerializer(serializers.ModelSerializer):
    """ Minimal user info, suitable for embedding in other serializers. """
    class Meta:
        model = User
        # id is handled implicitly by ModelSerializer based on model's PK
        fields = ['id', 'username', 'email'] # Adjust fields as needed for display


class UserSerializer(serializers.ModelSerializer):
    """ Full user info, typically for the logged-in user's status or profile. """
    class Meta:
        model = User
        # Exclude sensitive fields like password
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined']
        read_only_fields = ['id', 'is_staff', 'date_joined']


class RegisterSerializer(serializers.ModelSerializer):
    """ Serializer for user registration. """
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password], style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True, required=True, label="Confirm Password", style={'input_type': 'password'}
    )

    class Meta:
        model = User
        # Fields required for registration
        fields = ('username', 'email', 'password', 'password2', 'first_name', 'last_name')
        extra_kwargs = {
            # Make first/last name optional during registration
            'first_name': {'required': False},
            'last_name': {'required': False},
             # Ensure email and username are required and validated for uniqueness
            'email': {'required': True, 'allow_blank': False},
            'username': {'required': True, 'allow_blank': False},
        }

    def validate_email(self, value):
        """ Check if email is already taken (case-insensitive). """
        norm_email = User.objects.normalize_email(value)
        if User.objects.filter(email__iexact=norm_email).exists(): # Case-insensitive check
             logger.warning(f"Registration attempt with existing email: {norm_email}")
             raise serializers.ValidationError("A user with this email address already exists.")
        return norm_email

    def validate_username(self, value):
        """ Check if username is already taken (case-insensitive). """
        if User.objects.filter(username__iexact=value).exists(): # Case-insensitive check
            logger.warning(f"Registration attempt with existing username: {value}")
            raise serializers.ValidationError("A user with this username already exists.")
        # Add any other username validation rules here if needed
        return value

    def validate(self, attrs):
        """ Check that the two password entries match. """
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password2": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        """ Create and return a new user using the custom manager's create_user. """
        try:
            # Use the custom manager's create_user method which handles password hashing
            user = User.objects.create_user(
                username=validated_data['username'],
                email=validated_data['email'],
                password=validated_data['password'],
                first_name=validated_data.get('first_name', ''),
                last_name=validated_data.get('last_name', '')
            )
            logger.info(f"Successfully created user via serializer: {user.email}")
            return user
        except Exception as e:
             logger.error(f"Error in RegisterSerializer create method: {e}", exc_info=True)
             # Raise a validation error to signal failure back to the view
             raise serializers.ValidationError("Failed to create user due to an internal error.")


class LoginSerializer(serializers.Serializer):
    """ Serializer for user login validation. """
    email = serializers.EmailField(required=True, label="Email Address")
    password = serializers.CharField(
        required=True,
        write_only=True, # Never include password in response
        style={'input_type': 'password'},
        trim_whitespace=False # Allow passwords with leading/trailing whitespace
    )

    def validate_email(self, value):
         """ Normalize email for consistent lookup. """
         return User.objects.normalize_email(value)

    # Note: Actual authentication logic happens in the LoginView using authenticate()
