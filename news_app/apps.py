"""
App configuration for the news application.

This module defines the application configuration and handles
signal registration for the news_app.
"""
from django.apps import AppConfig


class NewsAppConfig(AppConfig):
    """
    Application configuration for the news_app.
    
    Handles app-specific settings and signal registration.
    """
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'news_app'
    
    def ready(self):
        """
        Method called when the app is ready.
        
        Imports and registers signal handlers for the application.
        This ensures signals are connected when Django starts.
        """
        import news_app.signals
