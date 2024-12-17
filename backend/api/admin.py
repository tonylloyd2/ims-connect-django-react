from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Idea, Vote, Team, Document,
    Comment, AuditLog, Notification, Milestone, Category, ChatMessage
)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'region', 'department', 'points')
    list_filter = ('role', 'region', 'department')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'region', 'department', 'points', 'expertise')}),
    )

@admin.register(Idea)
class IdeaAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'status', 'created_at', 'impact_score')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'description', 'tags')
    readonly_fields = ('impact_score',)

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'idea', 'created_at', 'value')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'idea__title')

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'idea', 'leader', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'leader__username')
    filter_horizontal = ('members',)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'idea', 'document_type', 'uploaded_by', 'uploaded_at')
    list_filter = ('document_type', 'uploaded_at')
    search_fields = ('title', 'uploaded_by__username')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'idea', 'created_at', 'parent')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'idea__title', 'content')

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp', 'idea')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__username', 'details')
    readonly_fields = ('timestamp',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'created_at', 'read')
    list_filter = ('type', 'created_at', 'read')
    search_fields = ('user__username', 'message')

@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ('title', 'idea', 'due_date', 'completed')
    list_filter = ('completed', 'due_date')
    search_fields = ('title', 'idea__title')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'description')
    search_fields = ('name', 'description')
    list_filter = ('parent',)

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('team', 'user', 'content', 'created_at', 'is_system_message')
    list_filter = ('team', 'user', 'is_system_message', 'created_at')
    search_fields = ('content',)
    readonly_fields = ('created_at',)
