"""
Form classes for the news application.

This module defines Django forms for user registration, article creation,
and newsletter management, including custom validation and widget configuration.
"""
from django import forms
from .models import Article, Newsletter, CustomUser, Publisher
from django.contrib.auth.forms import UserCreationForm


class CustomUserCreationForm(UserCreationForm):
    """
    Custom user registration form with role selection.
    
    Extends Django's built-in UserCreationForm to include role selection
    and uses the CustomUser model instead of the default User model.
    
    Attributes:
        ROLE_CHOICES (list): Available role options for new users
        role (ChoiceField): Field for selecting user role during registration
    """
    
    ROLE_CHOICES = [
        ('reader', 'Reader'),
        ('journalist', 'Journalist'),
        ('editor', 'Editor'),
    ]
    
    role = forms.ChoiceField(choices=ROLE_CHOICES)
    
    class Meta:
        """
        Metadata options for the CustomUserCreationForm.
        
        Attributes:
            model (Model): The CustomUser model this form is based on
            fields (tuple): Fields to include in the form in the specified order
        """
        model = CustomUser
        fields = ('username', 'email', 'role', 'password1', 'password2')


class ArticleForm(forms.ModelForm):
    """
    Form for creating and editing articles.
    
    Provides a form for journalists to create and edit articles with
    dynamic publisher filtering based on the user's associated publishers.
    
    The form includes custom widgets for better UI/UX and automatically
    filters the publisher choices to only show publishers the current
    user is associated with.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the form with dynamic publisher filtering.
        
        Filters the publisher queryset based on the user_publishers parameter
        to only show publishers that the current user is associated with.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments, including:
                user_publishers (QuerySet): Publishers available to the current user
        """
        user_publishers = kwargs.pop('user_publishers', None)
        super().__init__(*args, **kwargs)
        
        if user_publishers is not None:
            self.fields['publisher'].queryset = user_publishers
        else:
            self.fields['publisher'].queryset = Publisher.objects.none()
    
    class Meta:
        """
        Metadata options for the ArticleForm.
        
        Attributes:
            model (Model): The Article model this form is based on
            fields (list): Fields to include in the form
            widgets (dict): Custom widget configurations for form fields
            labels (dict): Custom labels for form fields
        """
        model = Article
        fields = ['title', 'content', 'publisher']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter article title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 10, 
                'placeholder': 'Write your article content here...'
            }),
            'publisher': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'publisher': 'Publishing House (optional - articles with publishers require approval)'
        }


class NewsletterForm(forms.ModelForm):
    """
    Form for creating and editing newsletters.
    
    Provides a form for journalists to create and edit newsletters
    with custom widgets for improved user experience.
    
    Newsletters can be associated with a publisher and include
    title, content, and publisher selection fields.
    """
    
    class Meta:
        """
        Metadata options for the NewsletterForm.
        
        Attributes:
            model (Model): The Newsletter model this form is based on
            fields (list): Fields to include in the form
            widgets (dict): Custom widget configurations for form fields
        """
        model = Newsletter
        fields = ['title', 'content', 'publisher']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter newsletter title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 8, 
                'placeholder': 'Write your newsletter content here...'
            }),
            'publisher': forms.Select(attrs={
                'class': 'form-control'
            })
        }