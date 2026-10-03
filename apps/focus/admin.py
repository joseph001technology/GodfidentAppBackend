from django.contrib import admin
from .models import (
    BlockedApp, BlockedWebsite, WhitelistApp, WhitelistWebsite,
    FocusSchedule, FocusSession, BlockedAttempt, WebsiteProtectionKey,
)


@admin.register(BlockedApp)
class BlockedAppAdmin(admin.ModelAdmin):
    list_display = ['app_name', 'package_name', 'user', 'is_active']
    search_fields = ['app_name', 'user__email']


@admin.register(BlockedWebsite)
class BlockedWebsiteAdmin(admin.ModelAdmin):
    list_display = ['domain', 'url', 'user', 'is_active']
    search_fields = ['domain', 'user__email']


@admin.register(WhitelistApp)
class WhitelistAppAdmin(admin.ModelAdmin):
    list_display = ['app_name', 'package_name', 'user']
    search_fields = ['app_name', 'user__email']


@admin.register(WhitelistWebsite)
class WhitelistWebsiteAdmin(admin.ModelAdmin):
    list_display = ['domain', 'user']


@admin.register(FocusSchedule)
class FocusScheduleAdmin(admin.ModelAdmin):
    list_display = ['user', 'day_of_week', 'start_time', 'end_time', 'is_active']
    list_filter = ['day_of_week']


@admin.register(FocusSession)
class FocusSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'started_at', 'duration_minutes', 'status', 'blocked_attempts']
    list_filter = ['status']


@admin.register(BlockedAttempt)
class BlockedAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'target_type', 'target_name', 'attempted_at']
    list_filter = ['target_type']


@admin.register(WebsiteProtectionKey)
class WebsiteProtectionKeyAdmin(admin.ModelAdmin):
    # The key itself is never stored; deleting a row here is the only way to
    # let a user create a new one (for example after a verified request).
    list_display = ['user', 'failed_attempts', 'locked_until', 'created_at']
    readonly_fields = ['key_hash']
    search_fields = ['user__email']
