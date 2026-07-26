from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'reading_streak', 'prayer_streak', 'focus_streak']
    search_fields = ['user__email']