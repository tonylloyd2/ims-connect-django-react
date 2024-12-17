from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.utils import timezone
from .models import (
    User, Idea, Vote, Team, Document, Comment,
    AuditLog, Notification, Milestone, Category
)
from .serializers import (
    UserSerializer, IdeaSerializer, VoteSerializer,
    TeamSerializer, DocumentSerializer, CommentSerializer,
    AuditLogSerializer, NotificationSerializer, MilestoneSerializer,
    CategorySerializer
)
from .permissions import (
    IsRegionalManager, IsGlobalManager, IsEmployee,
    IsIdeaCreator, CanManageIdea
)
from .utils import (
    get_similar_ideas, recommend_collaborators,
    calculate_idea_impact_score, get_trending_ideas,
    sync_offline_data
)
import logging

logger = logging.getLogger(__name__)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email', 'department', 'expertise']

    @action(detail=False, methods=['get'])
    def profile(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        user = request.user
        stats = {
            'ideas_count': Idea.objects.filter(creator=user).count(),
            'approved_ideas': Idea.objects.filter(creator=user, status='approved').count(),
            'teams_count': Team.objects.filter(Q(leader=user) | Q(members=user)).distinct().count(),
            'points': user.points if hasattr(user, 'points') else 0
        }
        return Response(stats)

    @action(detail=True, methods=['post'])
    def sync_offline_data(self, request, pk=None):
        user = self.get_object()
        if user != request.user:
            return Response(
                {"error": "Cannot sync offline data for other users"},
                status=status.HTTP_403_FORBIDDEN
            )
        sync_offline_data(request.data.get('offline_data', []), user)
        return Response({"status": "Offline data synced successfully"})

class VoteViewSet(viewsets.ModelViewSet):
    queryset = Vote.objects.all()
    serializer_class = VoteSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return Vote.objects.filter(Q(user=self.request.user) | Q(idea__creator=self.request.user))

class IdeaViewSet(viewsets.ModelViewSet):
    queryset = Idea.objects.all()
    serializer_class = IdeaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'tags']
    ordering_fields = ['created_at', 'impact_score', 'status']

    def get_queryset(self):
        if self.action == 'my_ideas':
            logger.info(f"Getting my_ideas for user {self.request.user.username}")
            ideas = Idea.objects.filter(creator=self.request.user)
            logger.info(f"Found {ideas.count()} ideas")
            return ideas
        return super().get_queryset()

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
        logger.info(f"Created new idea: {serializer.instance.title} by {self.request.user.username}")
        AuditLog.objects.create(
            user=self.request.user,
            action='create',
            details=f'Created new idea: {serializer.instance.title}',
            idea=serializer.instance
        )

    @action(detail=False, methods=['get'], url_path='my-ideas')
    def my_ideas(self, request):
        logger.info(f"my_ideas action called by {request.user.username}")
        queryset = self.get_queryset()
        logger.info(f"Raw queryset: {queryset.query}")
        logger.info(f"Ideas found: {[idea.title for idea in queryset]}")
        serializer = self.get_serializer(queryset, many=True)
        logger.info(f"Serialized data: {serializer.data}")
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def vote(self, request, pk=None):
        idea = self.get_object()
        if idea.votes.filter(user=request.user).exists():
            return Response(
                {"error": "Already voted for this idea"},
                status=status.HTTP_400_BAD_REQUEST
            )
        vote = Vote.objects.create(
            user=request.user,
            idea=idea,
            value=request.data.get('value', 1)
        )
        return Response(VoteSerializer(vote).data)

    @action(detail=True, methods=['get'])
    def similar_ideas(self, request, pk=None):
        idea = self.get_object()
        similar = get_similar_ideas(idea)
        return Response(IdeaSerializer(similar, many=True).data)

    @action(detail=True, methods=['get'])
    def recommended_collaborators(self, request, pk=None):
        idea = self.get_object()
        collaborators = recommend_collaborators(idea)
        return Response(UserSerializer(collaborators, many=True).data)

    @action(detail=False, methods=['get'])
    def trending(self, request):
        days = int(request.query_params.get('days', 7))
        ideas = get_trending_ideas(days)
        return Response(IdeaSerializer(ideas, many=True).data)

class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(leader=self.request.user)

    @action(detail=False, methods=['get'])
    def updates(self, request):
        user = request.user
        teams = Team.objects.filter(Q(leader=user) | Q(members=user))
        updates = []
        for team in teams:
            updates.append({
                'team_name': team.name,
                'message': f'Latest update for {team.name}',
                'created_at': timezone.now()
            })
        return Response(updates)

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        team = self.get_object()
        user_id = request.data.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            team.members.add(user)
            return Response(TeamSerializer(team).data)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        team = self.get_object()
        user_id = request.data.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            if user == team.leader:
                return Response(
                    {"error": "Cannot remove team leader"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            team.members.remove(user)
            return Response(TeamSerializer(team).data)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.read = True
        notification.save()
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        self.get_queryset().update(read=True)
        return Response({"status": "All notifications marked as read"})

class MilestoneViewSet(viewsets.ModelViewSet):
    queryset = Milestone.objects.all()
    serializer_class = MilestoneSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def mark_complete(self, request, pk=None):
        milestone = self.get_object()
        milestone.mark_complete()
        return Response(MilestoneSerializer(milestone).data)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.info("Fetching categories")
        queryset = Category.objects.all()
        logger.info(f"Found {queryset.count()} categories")
        return queryset

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['timestamp', 'action']

    @action(detail=False, methods=['get'])
    def recent(self, request):
        activities = self.get_queryset().filter(
            timestamp__gte=timezone.now() - timezone.timedelta(days=7)
        ).order_by('-timestamp')[:10]
        
        activity_list = []
        for activity in activities:
            activity_list.append({
                'description': activity.details,
                'created_at': activity.timestamp
            })
        return Response(activity_list)

    def get_queryset(self):
        if self.request.user.role == 'regional_manager':
            return AuditLog.objects.filter(
                Q(user__region=self.request.user.region) |
                Q(idea__creator__region=self.request.user.region)
            )
        elif self.request.user.role == 'employee':
            return AuditLog.objects.filter(user=self.request.user)
        return AuditLog.objects.all()
