# This file can be used to define Django signals for the 'app'.
# Signals allow certain senders to notify a set of receivers when certain actions occur.

# Example: Automatically setting permissions when a Page is created
# (Note: This logic is currently handled in the PageViewSet.perform_create for simplicity,
# but signals are an alternative.)

# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.conf import settings
# from .models import Page, PagePermission

# import logging
# logger = logging.getLogger(__name__)

# @receiver(post_save, sender=Page)
# def grant_owner_permissions_on_page_create(sender, instance, created, **kwargs):
#     """
#     Grants full permissions (VIEW, EDIT, MANAGE) to the owner
#     when a new Page is created.
#     """
#     if created and instance.owner:
#         try:
#             user = instance.owner
#             permissions_to_create = [
#                 PagePermission(page=instance, level=PagePermission.Level.VIEW, target_type=PagePermission.TargetType.USER, target_user=user, granted_by=user),
#                 PagePermission(page=instance, level=PagePermission.Level.EDIT, target_type=PagePermission.TargetType.USER, target_user=user, granted_by=user),
#                 PagePermission(page=instance, level=PagePermission.Level.MANAGE, target_type=PagePermission.TargetType.USER, target_user=user, granted_by=user),
#             ]
#             # Use bulk_create for efficiency, ignore conflicts just in case (though shouldn't happen on create)
#             PagePermission.objects.bulk_create(permissions_to_create, ignore_conflicts=True)
#             logger.info(f"Signal granted owner permissions for new page '{instance.slug}' to user '{user.email}'")
#         except Exception as e:
#             logger.error(f"Error in signal granting owner permissions for page {instance.slug}: {e}", exc_info=True)


# Remember to import this module in your app's AppConfig.ready() method
# in apps.py:
#
# def ready(self):
#     import app.signals