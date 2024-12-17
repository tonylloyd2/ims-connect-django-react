from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    User, Idea, Vote, Team, Document, Comment, 
    AuditLog, Notification, Milestone, Category, ChatMessage
)
import json

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'region', 
                 'department', 'points', 'expertise']
        read_only_fields = ['points']

class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'user', 'idea', 'content', 'created_at', 
                 'updated_at', 'parent', 'replies']
        read_only_fields = ['user']

    def get_replies(self, obj):
        if obj.replies.exists():
            return CommentSerializer(obj.replies.all(), many=True).data
        return []

class VoteSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Vote
        fields = ['id', 'user', 'idea', 'created_at', 'value']
        read_only_fields = ['user']

class DocumentSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)

    class Meta:
        model = Document
        fields = ['id', 'idea', 'title', 'file', 'document_type',
                 'uploaded_by', 'uploaded_at', 'version']
        read_only_fields = ['uploaded_by']

class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = ['id', 'idea', 'title', 'description', 'due_date',
                 'completed', 'completed_at']
        read_only_fields = ['completed_at']

class TeamSerializer(serializers.ModelSerializer):
    leader = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Team
        fields = ['id', 'name', 'idea', 'leader', 'members', 'created_at']
        read_only_fields = ['leader']

class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'parent', 'subcategories']

    def get_subcategories(self, obj):
        return CategorySerializer(obj.subcategories.all(), many=True).data

class ChatMessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['id', 'team', 'user', 'content', 'created_at', 'is_system_message']
        read_only_fields = ['user']

class IdeaSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    votes_count = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True, read_only=True)
    team = TeamSerializer(read_only=True)
    documents = DocumentSerializer(many=True, read_only=True)
    milestones = MilestoneSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    required_expertise = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Idea
        fields = ['id', 'creator', 'title', 'description', 'tags',
                 'status', 'created_at', 'updated_at', 'impact_score',
                 'implementation_cost', 'estimated_time', 'votes_count',
                 'comments', 'team', 'documents', 'milestones',
                 'category', 'is_cross_regional', 'required_expertise']
        read_only_fields = ['creator', 'impact_score']

    def get_votes_count(self, obj):
        count = obj.votes.count()
        return count

    def get_required_expertise(self, obj):
        try:
            if not obj.required_expertise:
                return []
            return json.loads(obj.required_expertise)
        except json.JSONDecodeError:
            return []

    def get_tags(self, obj):
        try:
            if not obj.tags:
                return []
            return json.loads(obj.tags)
        except json.JSONDecodeError:
            return []

    def validate(self, data):
        if self.instance and self.instance.status != data.get('status'):
            user = self.context['request'].user
            if user.role == 'employee' and data['status'] not in ['draft', 'submitted']:
                raise serializers.ValidationError(
                    "Employees can only set status to 'draft' or 'submitted'"
                )
        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        print(f"Serializing idea {instance.id}:")
        print(f"- Title: {instance.title}")
        print(f"- Category: {instance.category}")
        print(f"- Status: {instance.status}")
        print(f"- Required Expertise: {instance.required_expertise}")
        print(f"- Tags: {instance.tags}")
        return data

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'user', 'type', 'message', 'created_at',
                 'read', 'related_idea', 'related_team']
        read_only_fields = ['user']

class AuditLogSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'action', 'details', 'timestamp',
                 'idea', 'ip_address']
        read_only_fields = ['user', 'timestamp']
