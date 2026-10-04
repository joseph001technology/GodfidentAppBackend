from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='analytics-dashboard'),
    path('heatmap/', views.ReadingHeatmapView.as_view(), name='reading-heatmap'),
    path('weekly/', views.WeeklyReportView.as_view(), name='weekly-report'),
    path('monthly/', views.MonthlyReportView.as_view(), name='monthly-report'),
    path('log-reading/', views.LogReadingActivityView.as_view(), name='log-reading'),
    path('activity/', views.ActivityView.as_view(), name='analytics-activity'),
    path('overview/', views.OverviewView.as_view(), name='analytics-overview'),
    path('prayer/', views.PrayerAnalyticsView.as_view(), name='analytics-prayer'),
    path('focus/', views.FocusAnalyticsView.as_view(), name='analytics-focus'),
    path('notes/', views.NotesAnalyticsView.as_view(), name='analytics-notes'),
    path('reminders/', views.ReminderAnalyticsView.as_view(), name='analytics-reminders'),
    path('usage/', views.UsageAnalyticsView.as_view(), name='analytics-usage'),
    path('log-usage/', views.LogUsageView.as_view(), name='analytics-log-usage'),
]
