from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import CustomUser, Article, Publisher, Newsletter
from django.utils import timezone

class APITestCase(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser', 
            password='testpass123', 
            role='reader'
        )
        self.client.force_authenticate(user=self.user)
        
        self.publisher = Publisher.objects.create(name="Test Publisher")
        self.journalist = CustomUser.objects.create_user(
            username='testjournalist',
            password='testpass123',
            role='journalist'
        )
        self.article = Article.objects.create(
            title="Test Article",
            content="Test content",
            journalist=self.journalist,
            publisher=self.publisher,
            is_approved=True
        )
    
    def test_article_api_retrieval(self):
        response = self.client.get('/api/articles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_newsletter_api_retrieval(self):
        Newsletter.objects.create(
            title="Test Newsletter",
            content="Test content",
            created_by=self.journalist,
            is_published=True
        )
        response = self.client.get('/api/newsletters/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class ViewTests(TestCase):
    def setUp(self):
        self.reader = CustomUser.objects.create_user(
            username='testreader',
            password='testpass123',
            role='reader'
        )
        self.journalist = CustomUser.objects.create_user(
            username='testjournalist',
            password='testpass123',
            role='journalist'
        )
        self.editor = CustomUser.objects.create_user(
            username='testeditor',
            password='testpass123',
            role='editor'
        )
    
    def test_reader_dashboard_access(self):
        self.client.login(username='testreader', password='testpass123')
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
    
    def test_journalist_dashboard_access(self):
        self.client.login(username='testjournalist', password='testpass123')
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
    
    def test_editor_dashboard_access(self):
        self.client.login(username='testeditor', password='testpass123')
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
    
    def test_home_view_shows_approved_articles(self):
        Article.objects.create(
            title="Approved Article",
            content="Test content",
            journalist=self.journalist,
            is_approved=True
        )
        Article.objects.create(
            title="Unapproved Article",
            content="Test content",
            journalist=self.journalist,
            is_approved=False
        )
        
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Approved Article")
        self.assertNotContains(response, "Unapproved Article")

class PublisherTests(TestCase):
    def setUp(self):
        self.editor = CustomUser.objects.create_user(
            username='testeditor',
            password='testpass123',
            role='editor'
        )
    
    def test_publisher_creation(self):
        self.client.login(username='testeditor', password='testpass123')
        response = self.client.post('/publisher/register/', {
            'name': 'Test Publishing House',
            'description': 'Test description'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Publisher.objects.filter(name='Test Publishing House').exists())