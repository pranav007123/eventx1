from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()

# We will completely disable automatic profile creation since we're doing it explicitly
# in our views to handle phone numbers correctly.
# This was causing conflicts where a profile would be created with default values
# before our code could set the correct phone number.

# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     """Create a profile when a user is created, but only if it doesn't exist already."""
#     if created:
#         # Only create if a profile doesn't exist
#         if not Profile.objects.filter(user=instance).exists():
#             Profile.objects.create(user=instance)

# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     """Ensure user has a profile, but don't overwrite existing ones."""
#     # Only create if a profile doesn't exist
#     if not Profile.objects.filter(user=instance).exists():
#         Profile.objects.create(user=instance) 