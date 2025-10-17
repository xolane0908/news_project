"""
API ViewSets for the news application REST API.

This module provides REST API endpoints for articles and newsletters
using Django REST Framework ViewSets with role-based access control.
"""
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Article, Newsletter, Publisher, CustomUser
from .serializers import ArticleSerializer, NewsletterSerializer, PublisherSerializer, UserSerializer


class ArticleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Article objects via REST API.
    
    Provides CRUD operations for articles with role-based filtering:
    - Readers see only approved articles from their subscriptions
    - Journalists and editors see all approved articles
    
    Attributes:
        serializer_class (Serializer): ArticleSerializer for data serialization
        permission_classes (list): Requires authenticated users
    """
    
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Get the queryset of articles based on user role and permissions.
        
        Readers see articles from their subscribed publishers and journalists.
        Other roles see all approved articles.
        
        Returns:
            QuerySet: Filtered articles queryset ordered by creation date
        """
        user = self.request.user
        
        if user.role == 'reader':
            subscribed_publishers = user.subscribed_publishers.all()
            subscribed_journalists = user.subscribed_journalists.all()
            
            queryset = Article.objects.filter(
                is_approved=True
            ).filter(
                Q(publisher__in=subscribed_publishers) |
                Q(journalist__in=subscribed_journalists)
            )
        else:
            queryset = Article.objects.filter(is_approved=True)
        
        return queryset.order_by('-created_at')


class NewsletterViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Newsletter objects via REST API.
    
    Provides CRUD operations for newsletters with role-based filtering:
    - Readers see only published newsletters from their subscriptions
    - Journalists and editors see all published newsletters
    
    Attributes:
        serializer_class (Serializer): NewsletterSerializer for data serialization
        permission_classes (list): Requires authenticated users
    """
    
    serializer_class = NewsletterSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Get the queryset of newsletters based on user role and permissions.
        
        Readers see newsletters from their subscribed publishers and journalists.
        Other roles see all published newsletters.
        
        Returns:
            QuerySet: Filtered newsletters queryset ordered by creation date
        """
        user = self.request.user
        
        if user.role == 'reader':
            subscribed_publishers = user.subscribed_publishers.all()
            subscribed_journalists = user.subscribed_journalists.all()
            
            queryset = Newsletter.objects.filter(
                is_published=True
            ).filter(
                Q(publisher__in=subscribed_publishers) |
                Q(created_by__in=subscribed_journalists)
            )
        else:
            queryset = Newsletter.objects.filter(is_published=True)
        
        return queryset.order_by('-created_at')