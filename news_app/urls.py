"""
URL configuration for the news application.

This module defines the URL routes for the news portal application,
mapping URL patterns to their corresponding view functions.
"""
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Public routes
    path('', views.home, name='home'),
    
    # Authentication routes
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard and user management
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Article management routes
    path('articles/create/', views.create_article, name='create_article'),
    path('articles/<int:article_id>/', views.article_detail, name='article_detail'),
    path('articles/<int:article_id>/approve/', views.approve_article, name='approve_article'),
    path('articles/<int:article_id>/edit/', views.edit_article, name='edit_article'),
    path('articles/<int:article_id>/delete/', views.delete_article, name='delete_article'),
    
    # Newsletter management routes
    path('newsletter/create/', views.create_newsletter, name='create_newsletter'),
    path('newsletter/<int:newsletter_id>/edit/', views.edit_newsletter, name='edit_newsletter'),  
    path('newsletter/<int:newsletter_id>/delete/', views.delete_newsletter, name='delete_newsletter'),
    
    # Subscription management
    path('subscriptions/', views.manage_subscriptions, name='manage_subscriptions'),
    
    # Publisher management routes
    path('publisher/register/', views.register_publisher, name='register_publisher'),
    path('publisher/<int:publisher_id>/join/', views.join_publisher, name='join_publisher'),
    path('publisher/<int:publisher_id>/manage/', views.manage_publisher, name='manage_publisher'),
    path('publishers/', views.list_publishers, name='list_publishers'),
]
