"""
Serializer classes for the news application REST API.

This module defines Django REST Framework serializers for converting
model instances to JSON and validating incoming API data.
"""
from rest_framework import serializers
from .models import Article, Newsletter, Publisher, CustomUser


class PublisherSerializer(serializers.ModelSerializer):
    """
    Serializer for Publisher model.
    
    Serializes all fields of the Publisher model for API representation.
    """
    
    class Meta:
        """
        Metadata options for PublisherSerializer.
        
        Attributes:
            model (Model): Publisher model to serialize
            fields (str): Include all model fields in serialization
        """
        model = Publisher
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for CustomUser model.
    
    Serializes selected fields of the CustomUser model for safe API exposure.
    Excludes sensitive fields like passwords and permissions.
    """
    
    class Meta:
        """
        Metadata options for UserSerializer.
        
        Attributes:
            model (Model): CustomUser model to serialize
            fields (tuple): Specific fields to include in serialization
        """
        model = CustomUser
        fields = ('id', 'username', 'email', 'role', 'bio')


class ArticleSerializer(serializers.ModelSerializer):
    """
    Serializer for Article model with enhanced read-only fields.
    
    Includes computed fields for journalist and publisher names
    in addition to all model fields.
    
    Attributes:
        journalist_name (CharField): Read-only username of the journalist
        publisher_name (CharField): Read-only name of the publisher
    """
    
    journalist_name = serializers.CharField(source='journalist.username', read_only=True)
    publisher_name = serializers.CharField(source='publisher.name', read_only=True)
    
    class Meta:
        """
        Metadata options for ArticleSerializer.
        
        Attributes:
            model (Model): Article model to serialize
            fields (str): Include all model fields in serialization
        """
        model = Article
        fields = '__all__'


class NewsletterSerializer(serializers.ModelSerializer):
    """
    Serializer for Newsletter model with enhanced read-only fields.
    
    Includes computed fields for creator and publisher names
    in addition to all model fields.
    
    Attributes:
        created_by_name (CharField): Read-only username of the creator
        publisher_name (CharField): Read-only name of the publisher
    """
    
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    publisher_name = serializers.CharField(source='publisher.name', read_only=True)
    
    class Meta:
        """
        Metadata options for NewsletterSerializer.
        
        Attributes:
            model (Model): Newsletter model to serialize
            fields (str): Include all model fields in serialization
        """
        model = Newsletter
        fields = '__all__'