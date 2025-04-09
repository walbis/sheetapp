from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError(_('The given email must be set'))
        email = self.normalize_email(email)
        # Ensure username is provided, default if necessary before creating model instance
        username = extra_fields.pop('username', None)
        if not username:
             # Create a default username if not provided (e.g., for social auth flows later)
             # For createsuperuser, it's required via REQUIRED_FIELDS
             username = email.split('@')[0] # Example default derivation
             # Add some uniqueness if needed:
             # counter = 1
             # base_username = username
             # while self.model.objects.filter(username=username).exists():
             #     username = f"{base_username}{counter}"
             #     counter += 1

        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        # Ensure username is provided for createsuperuser compatibility
        if 'username' not in extra_fields or not extra_fields['username']:
             raise ValueError(_('Superuser must have a username.'))

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model using email as the unique identifier for authentication.
    The standard 'username' field is kept for compatibility with Django admin and other tools,
    and is required by createsuperuser command by default.
    """
    # Username field inherited from AbstractUser, ensure it remains unique.
    # We don't remove it to maintain compatibility, but login uses email.
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[AbstractUser.username_validator], # Keep default validators
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    # Email field is now the primary identifier and must be unique.
    email = models.EmailField(_('email address'), unique=True)

    # Set email as the field used for authentication.
    USERNAME_FIELD = 'email'
    # Fields required when using the 'createsuperuser' command.
    # Email and password are required by default. Username is needed here too.
    REQUIRED_FIELDS = ['username']

    # Use the custom manager defined above.
    objects = UserManager()

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        """Return the email address as the string representation."""
        return self.email

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user (usually first name)."""
        return self.first_name
