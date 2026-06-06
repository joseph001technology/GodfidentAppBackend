from django.db import models
from django.conf import settings


class ChatSession(models.Model):
    """A general AI chat session."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_sessions')
    title = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_sessions'
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.user.email}: {self.title or "Chat"}'


class ChatMessage(models.Model):
    """Individual message in a chat session."""
    ROLE_CHOICES = [('user', 'User'), ('assistant', 'Assistant')]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_messages'
        ordering = ['created_at']


class BibleStudySession(models.Model):
    """A structured Bible study session with context."""
    STUDY_TYPES = [
        ('verse', 'Verse Explanation'),
        ('chapter', 'Chapter Study'),
        ('topic', 'Topic Study'),
        ('character', 'Character Study'),
        ('passage', 'Passage Study'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='study_sessions')
    study_type = models.CharField(max_length=20, choices=STUDY_TYPES)
    query = models.TextField()  # The verse, topic, or character studied
    response = models.TextField()
    translation = models.CharField(max_length=10, default='KJV')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bible_study_sessions'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email}: {self.study_type} - {self.query[:50]}'
