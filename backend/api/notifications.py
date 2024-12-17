from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from celery import shared_task

@shared_task
def send_notification_email(subject, template_name, context, recipient_list):
    """Send an email notification using a template."""
    html_message = render_to_string(template_name, context)
    
    return send_mail(
        subject=subject,
        message='',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=recipient_list,
        html_message=html_message,
        fail_silently=False,
    )

def notify_idea_created(idea):
    """Notify relevant users when a new idea is created."""
    context = {
        'idea_title': idea.title,
        'idea_description': idea.description,
        'creator_name': idea.creator.get_full_name() or idea.creator.username,
    }
    
    # Get all users with appropriate roles
    recipients = [user.email for user in idea.creator.get_managers()]
    
    send_notification_email.delay(
        subject=f'New Idea Submitted: {idea.title}',
        template_name='emails/idea_created.html',
        context=context,
        recipient_list=recipients
    )

def notify_idea_status_change(idea, old_status):
    """Notify relevant users when an idea's status changes."""
    context = {
        'idea_title': idea.title,
        'old_status': old_status,
        'new_status': idea.status,
    }
    
    recipients = [idea.creator.email] + [user.email for user in idea.team.members.all()]
    
    send_notification_email.delay(
        subject=f'Idea Status Updated: {idea.title}',
        template_name='emails/idea_status_changed.html',
        context=context,
        recipient_list=recipients
    )

def notify_team_invitation(team, invitee):
    """Notify a user when they are invited to join a team."""
    context = {
        'team_name': team.name,
        'idea_title': team.idea.title,
        'inviter_name': team.leader.get_full_name() or team.leader.username,
    }
    
    send_notification_email.delay(
        subject=f'Invitation to Join Team: {team.name}',
        template_name='emails/team_invitation.html',
        context=context,
        recipient_list=[invitee.email]
    )

def notify_comment_added(comment):
    """Notify relevant users when a new comment is added to an idea."""
    context = {
        'idea_title': comment.idea.title,
        'commenter_name': comment.user.get_full_name() or comment.user.username,
        'comment_text': comment.text,
    }
    
    # Notify idea creator and team members
    recipients = [comment.idea.creator.email] + [
        user.email for user in comment.idea.team.members.all()
        if user != comment.user  # Don't notify the commenter
    ]
    
    send_notification_email.delay(
        subject=f'New Comment on Idea: {comment.idea.title}',
        template_name='emails/new_comment.html',
        context=context,
        recipient_list=recipients
    )
