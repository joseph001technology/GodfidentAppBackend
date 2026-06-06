from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='analytics-dashboard'),
    path('heatmap/', views.ReadingHeatmapView.as_view(), name='reading-heatmap'),
    path('weekly/', views.WeeklyReportView.as_view(), name='weekly-report'),
    path('monthly/', views.MonthlyReportView.as_view(), name='monthly-report'),
    path('log-reading/', views.LogReadingActivityView.as_view(), name='log-reading'),
]
