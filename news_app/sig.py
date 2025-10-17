from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
import requests 
from datetime import datetime
from .models import Article

@receiver(post_save, sender=Article)