"""Celery app configuration for Godfident.

This module configures Celery for background task processing.
Run worker: celery -A godfident worker -l info
Run beat:  celery -A godfident beat -l info
"""
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'godfident.settings')

app = Celery('godfident')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()