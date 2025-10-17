"""
Data models for the news application.

This module defines the core database models for the news portal application,
including users, publishers, articles, and newsletters.
"""
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class Publisher(models.Model):
    """
    Represents a publishing house that can employ editors and journalists.
    
    Publishers can have multiple editors and journalists, and articles
    associated with a publisher require editorial approval.
    
    Attributes:
        name (CharField): The name of the publishing house
        description (TextField): Optional description of the publisher
        created_at (DateTimeField): Timestamp of when the publisher was created
        is_approved (BooleanField): Whether the publisher is approved in the system
        owner (ForeignKey): The editor user who owns this publishing house
        editors (ManyToManyField): Editors who can manage this publishing house
        journalists (ManyToManyField): Journalists associated with this publisher
    """
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    owner = models.ForeignKey(
        'CustomUser',
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'editor'},
        related_name='owned_publishers',
        null=True,
        blank=True
    )
    editors = models.ManyToManyField(
        'CustomUser',
        related_name='publishers',
        limit_choices_to={'role': 'editor'},
        blank=True
    )
    journalists = models.ManyToManyField(
        'CustomUser',
        related_name='associated_publishers',
        limit_choices_to={'role': 'journalist'},
        blank=True
    )
    
    def __str__(self):
        """String representation of the Publisher model."""
        return self.name


class CustomUser(AbstractUser):
    """
    Custom user model extending Django's AbstractUser with role-based functionality.
    
    This model adds role-based access control and subscription capabilities
    to the standard Django user model.
    
    Attributes:
        role (CharField): User's role in the system (reader, journalist, editor)
        bio (TextField): Optional biography of the user
        subscribed_publishers (ManyToManyField): Publishers the user follows
        subscribed_journalists (ManyToManyField): Journalists the user follows
    """
    
    ROLE_CHOICES = [
        ('reader', 'Reader'),
        ('journalist', 'Journalist'),
        ('editor', 'Editor'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='reader')
    bio = models.TextField(blank=True)
    
    subscribed_publishers = models.ManyToManyField(
        Publisher,
        related_name='subscribers',
        blank=True
    )
    subscribed_journalists = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='subscribers',
        blank=True,
        limit_choices_to={'role': 'journalist'}
    )
    
    def save(self, *args, **kwargs):
        """
        Override save method to automatically assign users to groups.
        
        When a new user is created, they are automatically added to a group
        matching their role. Journalists have their subscriptions cleared
        as they are content creators, not subscribers.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        creating = self._state.adding
        super().save(*args, **kwargs)
        
        if creating:
            group, created = Group.objects.get_or_create(name=self.role.capitalize())
            self.groups.add(group)
            
            if self.role == 'journalist':
                self.subscribed_publishers.clear()
                self.subscribed_journalists.clear()
        
    def __str__(self):
        """String representation showing username and role."""
        return f"{self.username} ({self.get_role_display()})"


class Subscription(models.Model):
    """
    Tracks subscription relationships between readers and content producers.
    
    Readers can subscribe to either publishers or individual journalists.
    Each subscription is unique per reader-publisher or reader-journalist pair.
    
    Attributes:
        reader (ForeignKey): The user who is subscribing
        publisher (ForeignKey): Optional publisher being subscribed to
        journalist (ForeignKey): Optional journalist being subscribed to
        created_at (DateTimeField): When the subscription was created
    """
    
    reader = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'reader'}
    )
    publisher = models.ForeignKey(
        Publisher, 
        null=True, 
        blank=True,
        on_delete=models.CASCADE
    )
    journalist = models.ForeignKey(
        CustomUser, 
        null=True, 
        blank=True,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'journalist'},
        related_name='journalist_subscriptions'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Metadata options for the Subscription model."""
        unique_together = [
            ('reader', 'publisher'),
            ('reader', 'journalist'),
        ]

    def __str__(self):
        """String representation showing the subscription relationship."""
        if self.publisher:
            return f"{self.reader.username} -> {self.publisher.name}"
        elif self.journalist:
            return f"{self.reader.username} -> {self.journalist.username}"
        return f"{self.reader.username} subscription"


@receiver(post_save, sender=CustomUser)
def set_user_permissions(sender, instance, created, **kwargs):
    """
    Signal receiver to set up user permissions when a new user is created.
    
    This function automatically assigns appropriate permissions to users
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


class Article(models.Model):
    """
    Represents a news article in the system.
    
    Articles can be written by journalists and may be associated with a publisher.
    Articles associated with publishers require editorial approval before publication.
    
    Attributes:
        title (CharField): The headline of the article
        content (TextField): The main body content of the article
        journalist (ForeignKey): The journalist who wrote the article
        publisher (ForeignKey): Optional publishing house associated with the article
        created_at (DateTimeField): When the article was created
        updated_at (DateTimeField): When the article was last updated
        is_approved (BooleanField): Whether the article has been approved for publication
        approved_by (ForeignKey): The editor who approved the article
        approved_at (DateTimeField): When the article was approved
    """
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    journalist = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'journalist'},
        related_name='authored_articles'
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='articles'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_articles',
        limit_choices_to={'role': 'editor'}
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    def requires_approval(self):
        """
        Check if this article requires editorial approval.
        
        Returns:
            bool: True if the article is associated with a publisher and requires approval
        """
        return self.publisher is not None
    
    class Meta:
        """Metadata options including custom permissions."""
        permissions = [
            ("approve_article", "Can approve articles"),
        ]
    
    def __str__(self):
        """String representation showing the article title."""
        return self.title


class Newsletter(models.Model):
    """
    Represents a newsletter that can be sent to subscribers.
    
    Newsletters are created by journalists and can be associated with a publisher.
    They are separate from articles and have different publication workflows.
    
    Attributes:
        title (CharField): The title of the newsletter
        content (TextField): The main content of the newsletter
        created_by (ForeignKey): The journalist who created the newsletter
        publisher (ForeignKey): Optional publishing house associated with the newsletter
        created_at (DateTimeField): When the newsletter was created
        is_published (BooleanField): Whether the newsletter has been published
    """
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'journalist'},
        related_name='authored_newsletters'
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='newsletters'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=False)
    
    def __str__(self):
        """String representation showing the newsletter title."""
        return self.title
