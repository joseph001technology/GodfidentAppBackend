from django.contrib import admin
from .models import Reminder, ReminderCategory, ReminderHistory


@admin.register(ReminderCategory)
class ReminderCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'color']
    search_fields = ['name', 'user__email']


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'date', 'time', 'repeat', 'status']
    list_filter = ['status', 'repeat', 'date']
    search_fields = ['title', 'user__email']
    date_hierarchy = 'date'


@admin.register(ReminderHistory)
class ReminderHistoryAdmin(admin.ModelAdmin):
    list_display = ['reminder', 'action', 'timestamp']
    list_filter = ['action']
