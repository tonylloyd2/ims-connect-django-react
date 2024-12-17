from django.db.models import Q, Count
from .models import Idea, User, Team
from django.utils import timezone
from datetime import timedelta

def get_similar_ideas(idea, limit=5):
    """Find similar ideas based on title, description, and tags."""
    return Idea.objects.filter(
        Q(title__icontains=idea.title) |
        Q(description__icontains=idea.description) |
        Q(tags__overlap=idea.tags)
    ).exclude(id=idea.id)[:limit]

def recommend_collaborators(idea, limit=5):
    """Recommend potential collaborators based on expertise and past contributions."""
    # Find users with similar expertise (based on tags)
    users_with_expertise = User.objects.filter(
        expertise__overlap=idea.tags
    ).exclude(id=idea.creator.id)

    # Find users who have contributed to similar ideas
    similar_ideas = get_similar_ideas(idea)
    users_with_similar_contributions = User.objects.filter(
        Q(created_ideas__in=similar_ideas) |
        Q(votes__idea__in=similar_ideas) |
        Q(comments__idea__in=similar_ideas)
    ).distinct().exclude(id=idea.creator.id)

    # Combine and sort by points
    potential_collaborators = (users_with_expertise | users_with_similar_contributions).distinct()
    return potential_collaborators.order_by('-points')[:limit]

def calculate_idea_impact_score(idea):
    """Calculate an impact score based on various metrics."""
    # Base score from votes
    vote_score = idea.votes.count() * 2

    # Comment engagement score
    comment_score = idea.comments.count()

    # Team size score
    team_size = idea.team.members.count() if hasattr(idea, 'team') else 0
    team_score = team_size * 1.5

    # Time factor (newer ideas get a slight boost)
    days_old = (timezone.now() - idea.created_at).days
    time_factor = max(1, 2 - (days_old / 30))  # Decay over 30 days

    # Implementation progress score
    progress_scores = {
        'draft': 1,
        'submitted': 2,
        'under_review': 3,
        'approved': 4,
        'in_progress': 5,
        'implemented': 6
    }
    progress_score = progress_scores.get(idea.status, 1)

    # Calculate final score
    total_score = (vote_score + comment_score + team_score + progress_score) * time_factor
    return round(total_score, 2)

def get_trending_ideas(days=7, limit=5):
    """Get trending ideas based on recent activity."""
    recent_date = timezone.now() - timedelta(days=days)
    
    return Idea.objects.annotate(
        recent_votes=Count('votes', filter=Q(votes__created_at__gte=recent_date)),
        recent_comments=Count('comments', filter=Q(comments__created_at__gte=recent_date))
    ).filter(
        Q(created_at__gte=recent_date) |
        Q(recent_votes__gt=0) |
        Q(recent_comments__gt=0)
    ).order_by('-recent_votes', '-recent_comments', '-created_at')[:limit]

def sync_offline_data(offline_data, user):
    """Sync offline data when user comes back online."""
    for item in offline_data:
        if item['type'] == 'idea':
            Idea.objects.create(
                creator=user,
                title=item['title'],
                description=item['description'],
                tags=item['tags'],
                created_at=item['timestamp']
            )
        elif item['type'] == 'vote':
            idea = Idea.objects.get(id=item['idea_id'])
            if not idea.votes.filter(user=user).exists():
                idea.votes.create(user=user, created_at=item['timestamp'])
        elif item['type'] == 'comment':
            idea = Idea.objects.get(id=item['idea_id'])
            idea.comments.create(
                user=user,
                content=item['content'],
                created_at=item['timestamp']
            )
