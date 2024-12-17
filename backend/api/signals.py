from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from .models import Idea, Vote, Team, Comment, User, Notification, AuditLog

@receiver(post_save, sender=Idea)
def idea_created(sender, instance, created, **kwargs):
    if created:
        # Award points for creating an idea
        instance.creator.points += 10
        instance.creator.save()

        # Create audit log
        AuditLog.objects.create(
            user=instance.creator,
            action='create',
            details=f'Created new idea: {instance.title}',
            idea=instance
        )

@receiver(post_save, sender=Vote)
def vote_recorded(sender, instance, created, **kwargs):
    if created:
        # Award points for voting
        instance.user.points += 2
        instance.user.save()

        # Create notification for idea creator
        Notification.objects.create(
            user=instance.idea.creator,
            type='vote_received',
            message=f'{instance.user.username} voted for your idea: {instance.idea.title}',
            related_idea=instance.idea
        )

        # Check if idea has reached minimum vote threshold (3 votes)
        if instance.idea.votes.count() >= 3:
            # Notify regional managers
            regional_managers = User.objects.filter(
                role='regional_manager',
                region=instance.idea.creator.region
            )
            for manager in regional_managers:
                Notification.objects.create(
                    user=manager,
                    type='idea_ready_for_review',
                    message=f'Idea "{instance.idea.title}" has reached review threshold',
                    related_idea=instance.idea
                )

@receiver(post_save, sender=Comment)
def comment_created(sender, instance, created, **kwargs):
    if created:
        # Award points for commenting
        instance.user.points += 5
        instance.user.save()

        # Create notification for idea creator
        if instance.idea.creator != instance.user:
            Notification.objects.create(
                user=instance.idea.creator,
                type='new_comment',
                message=f'{instance.user.username} commented on your idea: {instance.idea.title}',
                related_idea=instance.idea
            )

@receiver(m2m_changed, sender=Team.members.through)
def team_member_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action == "post_add":
        for user_id in pk_set:
            user = User.objects.get(id=user_id)
            # Create notification for new team member
            Notification.objects.create(
                user=user,
                type='team_invite',
                message=f'You have been added to team: {instance.name}',
                related_team=instance
            )
            # Award points for joining a team
            user.points += 5
            user.save()

@receiver(post_save, sender=Idea)
def idea_status_changed(sender, instance, created, **kwargs):
    if not created and instance.tracker.has_changed('status'):
        # Create notification for status change
        Notification.objects.create(
            user=instance.creator,
            type=f'idea_{instance.status}',
            message=f'Your idea "{instance.title}" has been {instance.status}',
            related_idea=instance
        )
        
        # Award points for approved ideas
        if instance.status == 'approved':
            instance.creator.points += 20
            instance.creator.save()
