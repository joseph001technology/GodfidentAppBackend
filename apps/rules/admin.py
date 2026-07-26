from django.contrib import admin
from .models import Rule, RuleCategory, RuleCompletion


@admin.register(RuleCategory)
class RuleCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'color']
    search_fields = ['name', 'user__email']


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'category', 'is_pinned', 'is_favorite', 'is_archived', 'order']
    list_filter = ['is_pinned', 'is_favorite', 'is_archived', 'is_daily']
    search_fields = ['title', 'user__email']


@admin.register(RuleCompletion)
class RuleCompletionAdmin(admin.ModelAdmin):
    list_display = ['rule', 'completed_date', 'is_completed']
    list_filter = ['is_completed']
