from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AppConfig(AppConfig):
    """
    Application configuration for the 'app' module.
    Specifies the default auto field and the application name.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
    verbose_name = _("Sheet Application") # User-friendly name for the admin

    def ready(self):
        """
        Called when the application is ready.
        Use this method to import signals or perform other setup tasks.
        """
        try:
            # Import signals here if you have a signals.py file
            import app.signals
            # print("App signals imported successfully.") # Optional debug print
        except ImportError:
            # No signals.py file found or error importing it
            pass
        except Exception as e:
            # Catch other potential errors during import
            print(f"Error importing app signals: {e}")