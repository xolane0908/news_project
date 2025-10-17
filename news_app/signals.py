"""
Signal handlers for the news application.

This module contains signal receivers that perform automatic
actions when models are saved or updated.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission
from .models import CustomUser


@receiver(post_save, sender=CustomUser)
def set_user_permissions(sender, instance, created, **kwargs):
    """
    Signal receiver to set up user permissions when a new user is created.
    
    Automatically assigns users to groups and sets permissions
    based on their role when they are first created.
    
    Args:
        sender: The model class that sent the signal
        instance: The actual instance being saved
        created (bool): True if a new record was created
        **kwargs: Additional keyword arguments
    """
    if created:
        group, created = Group.objects.get_or_create(name=instance.role.capitalize())
        instance.groups.add(group)
        
        if instance.role == 'journalist':
            try:
                from django.contrib.contenttypes.models import ContentType
                from django.contrib.auth.models import Permission
                
                perms = Permission.objects.filter(
                    codename__in=[
                        'add_article', 'change_article', 'delete_article', 'view_article',
                        'add_newsletter', 'change_newsletter', 'delete_newsletter', 'view_newsletter'
                    ]
                )
                group.permissions.add(*perms)
            except Exception as e:
                print(f"Error setting journalist permissions: {e}")
        
        elif instance.role == 'editor':
            try:
                from django.contrib.auth.models import Permission
                
                perms = Permission.objects.filter(
                    codename__in=[
                        'change_article', 'view_article', 'change_newsletter', 
                        'view_newsletter', 'approve_article'
                    ]
                )
                group.permissions.add(*perms)
            except Exception as e:
                print(f"Error setting editor permissions: {e}")