from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('translations', views.TranslationViewSet, basename='translation')
router.register('books', views.BookViewSet, basename='book')
router.register('bookmarks', views.BookmarkViewSet, basename='bookmark')
router.register('highlights', views.HighlightViewSet, basename='highlight')
router.register('notes', views.VerseNoteViewSet, basename='verse-note')
router.register('favorites', views.FavoriteVerseViewSet, basename='favorite-verse')
router.register('collections', views.VerseCollectionViewSet, basename='verse-collection')
router.register('reading-goals', views.ReadingGoalViewSet, basename='reading-goal')

urlpatterns = [
    path('', include(router.urls)),
    path('verse/', views.VerseView.as_view(), name='verse'),
    path('chapter/', views.ChapterView.as_view(), name='chapter'),
    path('parallel/', views.ParallelVerseView.as_view(), name='parallel'),
    path('cross-references/', views.CrossReferenceView.as_view(), name='cross-references'),
    path('search/', views.SearchVerseView.as_view(), name='search'),
    path('reading-progress/', views.ReadingProgressView.as_view(), name='reading-progress'),
    path('save-progress/', views.SaveReadingProgressView.as_view(), name='save-reading-progress'),
    path('reading-history/', views.ReadingHistoryView.as_view(), name='reading-history'),
    path('verse-of-the-day/', views.VerseOfTheDayView.as_view(), name='verse-of-the-day'),
]
