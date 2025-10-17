"""
Admin configuration for the news application.

This module registers models with the Django admin interface and
configures custom admin classes for enhanced management capabilities.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Publisher, Article, Newsletter


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Admin interface configuration for CustomUser model.
    
    Extends the default UserAdmin to include custom fields
    and filtering options for the CustomUser model.
    """
    
    list_display = ('username', 'email', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'bio', 'subscribed_publishers', 'subscribed_journalists')
        }),
    )
    
    
@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    """
    Admin interface configuration for Publisher model.
    
    Provides basic admin functionality for managing publishing houses.
    """
    
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """
    Admin interface configuration for Article model.
    
    Provides enhanced article management with custom actions
    and filtering options for editorial workflow.
    """
    
    list_display = ('title', 'journalist', 'publisher', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'publisher', 'created_at')
    search_fields = ('title', 'content')
    actions = ['approve_articles']
    
    def approve_articles(self, request, queryset):
        """
        Custom admin action to approve multiple articles at once.
        
        Args:
            request: The current request object
            queryset: Articles selected for approval
        """
        for article in queryset:
            article.is_approved = True
            article.approved_by = request.user
            article.save()
        self.message_user(request, f"{queryset.count()} articles approved successfully.")
    
    approve_articles.short_description = "Approve selected articles"


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    """
    Admin interface configuration for Newsletter model.
    
    Provides admin functionality for managing newsletters
    with filtering and search capabilities.
    """
    
    list_display = ('title', 'created_by', 'publisher', 'is_published', 'created_at')
    list_filter = ('is_published', 'publisher', 'created_at')
    search_fields = ('title', 'content')