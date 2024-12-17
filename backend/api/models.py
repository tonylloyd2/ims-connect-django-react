from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
import json

class User(AbstractUser):
    ROLE_CHOICES = [
        ('employee', 'Employee'),
        ('regional_manager', 'Regional Manager'),
        ('global_manager', 'Global Manager'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    region = models.CharField(max_length=100, null=True, blank=True)
    department = models.CharField(max_length=100)
    points = models.IntegerField(default=0)
    expertise = models.TextField(default='[]')  # Store as JSON string
    offline_data = models.TextField(null=True, blank=True)  # Store as JSON string

    def set_expertise(self, expertise_list):
        self.expertise = json.dumps(expertise_list)

    def get_expertise(self):
        return json.loads(self.expertise)

class Idea(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('in_progress', 'In Progress'),
        ('implemented', 'Implemented'),
    ]

    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_ideas')
    title = models.CharField(max_length=200)
    description = models.TextField()
    tags = models.TextField(default='[]')  # Store as JSON string
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    impact_score = models.FloatField(default=0.0)
    implementation_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estimated_time = models.DurationField(null=True, blank=True)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, related_name='ideas')
    is_cross_regional = models.BooleanField(default=False)
    required_expertise = models.TextField(default='[]')  # Store as JSON string

    def set_tags(self, tags_list):
        self.tags = json.dumps(tags_list)

    def get_tags(self):
        return json.loads(self.tags)

    def get_required_expertise(self):
        return json.loads(self.required_expertise)

    def set_required_expertise(self, expertise_list):
        self.required_expertise = json.dumps(expertise_list)

class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='votes')
    idea = models.ForeignKey(Idea, on_delete=models.CASCADE, related_name='votes')
    created_at = models.DateTimeField(auto_now_add=True)
    value = models.IntegerField(default=1)

    class Meta:
        unique_together = ('user', 'idea')

class Team(models.Model):
    name = models.CharField(max_length=100)
    idea = models.OneToOneField(Idea, on_delete=models.CASCADE, related_name='team')
    leader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='led_teams')
    members = models.ManyToManyField(User, related_name='teams')
    created_at = models.DateTimeField(auto_now_add=True)

class ChatMessage(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_system_message = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='subcategories')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'categories'

class Document(models.Model):
    DOCUMENT_TYPES = [
        ('requirement', 'Requirement'),
        ('design', 'Design'),
        ('implementation', 'Implementation'),
        ('other', 'Other'),
    ]

    idea = models.ForeignKey(Idea, on_delete=models.CASCADE, related_name='documents', null=True, blank=True)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='documents/')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, default='other')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    version = models.CharField(max_length=20, default='1.0')

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    idea = models.ForeignKey(Idea, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')

class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=50)
    details = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    idea = models.ForeignKey(Idea, on_delete=models.CASCADE, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=50)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    related_idea = models.ForeignKey(Idea, on_delete=models.CASCADE, null=True, blank=True)
    related_team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True)

class Milestone(models.Model):
    idea = models.ForeignKey(Idea, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateTimeField()
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    def mark_complete(self):
        self.completed = True
        self.completed_at = timezone.now()
        self.save()
