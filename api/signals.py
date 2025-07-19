from django.db.models.signals import post_delete
from django.dispatch import receiver

@receiver(post_delete)
def delete_user_on_profile_delete(sender, instance, **kwargs):
    # This signal is generic and will be connected specifically in apps.py
    if hasattr(instance, 'user') and instance.user:
        instance.user.delete()
