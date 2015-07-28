from users.models import StacksyncUser, StacksyncWorkspace
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=StacksyncUser)
def create_default_workspace_for_user(sender, instance, created, **kwargs):
    if created:
        StacksyncWorkspace.objects.create_workspace(instance)