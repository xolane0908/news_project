"""
REST API URL configuration for the news application.

This module defines the URL routes for the REST API endpoints
using Django REST Framework's router for automatic URL generation.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import ArticleViewSet, NewsletterViewSet

# Create a router and register our ViewSets with it
router = DefaultRouter()
router.register(r'articles', ArticleViewSet, basename='article')
router.register(r'newsletters', NewsletterViewSet, basename='newsletter')

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
]
