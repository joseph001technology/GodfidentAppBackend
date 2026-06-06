from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('sessions', views.ChatSessionViewSet, basename='chat-session')

urlpatterns = [
    path('chat/', views.ChatView.as_view(), name='ai-chat'),
    path('explain-verse/', views.ExplainVerseView.as_view(), name='explain-verse'),
    path('explain-chapter/', views.ExplainChapterView.as_view(), name='explain-chapter'),
    path('topic-study/', views.TopicStudyView.as_view(), name='topic-study'),
    path('character-study/', views.CharacterStudyView.as_view(), name='character-study'),
    path('daily-encouragement/', views.DailyEncouragementView.as_view(), name='daily-encouragement'),
    path('prayer-assistance/', views.PrayerAssistanceView.as_view(), name='prayer-assistance'),
    path('study-history/', views.StudyHistoryView.as_view(), name='study-history'),
    path('', include(router.urls)),
]
