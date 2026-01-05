"""
Gamification Notifications

Notifications for achievements, level ups, streaks, and other gamification events.
"""

import logging
from datetime import datetime
from typing import Optional

from .models import UserBadge, UserChallenge, UserReward

logger = logging.getLogger(__name__)


def send_level_up_notification(
    user_id: str,
    new_level: int,
    storage,
):
    """
    Send level up notification.

    Args:
        user_id: User ID
        new_level: New level reached
        storage: Storage backend
    """
    from .levels import LevelService

    level_service = LevelService(storage)
    level = level_service.get_level(new_level)

    if not level:
        return

    # Create notification
    notification = {
        'type': 'level_up',
        'title': f'🎉 Level Up! You reached Level {new_level}',
        'message': f'Congratulations! You are now a {level.title}',
        'icon': level.icon,
        'data': {
            'level': new_level,
            'level_name': level.name,
            'title': level.title,
            'rewards': level.reward_description,
            'unlocks': level.unlocks,
        },
        'priority': 'high',
        'show_celebration': True,
        'celebration_type': 'confetti',
    }

    _send_notification(user_id, notification, storage)


def send_badge_earned_notification(
    user_id: str,
    user_badge: UserBadge,
    storage,
):
    """
    Send badge earned notification.

    Args:
        user_id: User ID
        user_badge: Earned badge
        storage: Storage backend
    """
    notification = {
        'type': 'badge_earned',
        'title': f'{user_badge.badge_icon} Badge Earned!',
        'message': f'You earned the "{user_badge.badge_title}" badge',
        'icon': user_badge.badge_icon,
        'data': {
            'badge_id': user_badge.badge_id,
            'badge_key': user_badge.badge_key,
            'badge_title': user_badge.badge_title,
            'badge_tier': user_badge.badge_tier,
            'xp_earned': user_badge.xp_earned,
        },
        'priority': 'high',
        'show_celebration': True,
        'celebration_type': 'badge_reveal',
    }

    _send_notification(user_id, notification, storage)


def send_streak_milestone_notification(
    user_id: str,
    milestone: int,
    storage,
):
    """
    Send streak milestone notification.

    Args:
        user_id: User ID
        milestone: Milestone achieved (e.g., 7, 30, 100)
        storage: Storage backend
    """
    milestone_messages = {
        7: ('🔥 Week Warrior!', 'Amazing! You maintained a 7-day learning streak'),
        30: ('🔥 Month Master!', 'Incredible! 30 days of consistent learning'),
        50: ('🔥 Unstoppable!', 'Wow! 50 days of dedication'),
        100: ('🔥 Century Club!', 'Legendary! 100-day streak achieved'),
        200: ('🔥 Elite Learner!', 'Extraordinary! 200 days strong'),
        365: ('🔥 Year of Excellence!', 'Phenomenal! A full year of learning'),
        500: ('🔥 Unstoppable Legend!', 'Unbelievable! 500-day streak'),
        1000: ('🔥 Eternal Scholar!', 'Impossible! 1000-day streak reached'),
    }

    title, message = milestone_messages.get(
        milestone,
        ('🔥 Streak Milestone!', f'Congratulations on your {milestone}-day streak')
    )

    notification = {
        'type': 'streak_milestone',
        'title': title,
        'message': message,
        'icon': '🔥',
        'data': {
            'milestone': milestone,
        },
        'priority': 'high',
        'show_celebration': True,
        'celebration_type': 'fireworks',
    }

    _send_notification(user_id, notification, storage)


def send_streak_at_risk_notification(
    user_id: str,
    current_streak: int,
    storage,
):
    """
    Send notification when streak is at risk.

    Args:
        user_id: User ID
        current_streak: Current streak length
        storage: Storage backend
    """
    notification = {
        'type': 'streak_at_risk',
        'title': '⚠️ Streak at Risk!',
        'message': f'Your {current_streak}-day streak is at risk. Learn something today!',
        'icon': '⚠️',
        'data': {
            'current_streak': current_streak,
        },
        'priority': 'normal',
        'action_url': '/learn',
        'action_text': 'Start Learning',
    }

    _send_notification(user_id, notification, storage)


def send_challenge_complete_notification(
    user_id: str,
    user_challenge: UserChallenge,
    storage,
):
    """
    Send challenge completion notification.

    Args:
        user_id: User ID
        user_challenge: Completed challenge
        storage: Storage backend
    """
    notification = {
        'type': 'challenge_complete',
        'title': '🏆 Challenge Completed!',
        'message': f'You completed: {user_challenge.challenge_title}',
        'icon': '🏆',
        'data': {
            'challenge_id': user_challenge.challenge_id,
            'challenge_title': user_challenge.challenge_title,
            'xp_earned': user_challenge.xp_earned,
        },
        'priority': 'normal',
        'show_celebration': True,
        'celebration_type': 'stars',
    }

    _send_notification(user_id, notification, storage)


def send_reward_redeemed_notification(
    user_id: str,
    user_reward: UserReward,
    storage,
):
    """
    Send reward redemption notification.

    Args:
        user_id: User ID
        user_reward: Redeemed reward
        storage: Storage backend
    """
    notification = {
        'type': 'reward_redeemed',
        'title': '🎁 Reward Redeemed!',
        'message': f'You redeemed: {user_reward.reward_title}',
        'icon': '🎁',
        'data': {
            'reward_id': user_reward.reward_id,
            'reward_title': user_reward.reward_title,
            'redemption_code': user_reward.redemption_code,
            'instructions': user_reward.instructions,
        },
        'priority': 'high',
        'action_url': f'/game/rewards/{user_reward.id}',
        'action_text': 'View Details',
    }

    _send_notification(user_id, notification, storage)


def send_daily_challenge_notification(
    user_id: str,
    storage,
):
    """
    Send daily challenge reminder.

    Args:
        user_id: User ID
        storage: Storage backend
    """
    notification = {
        'type': 'daily_challenge',
        'title': '🎯 New Daily Challenges!',
        'message': 'Check out today\'s challenges and earn bonus XP',
        'icon': '🎯',
        'priority': 'low',
        'action_url': '/game/challenges',
        'action_text': 'View Challenges',
    }

    _send_notification(user_id, notification, storage)


def send_leaderboard_rank_up_notification(
    user_id: str,
    new_rank: int,
    leaderboard_type: str,
    storage,
):
    """
    Send leaderboard rank improvement notification.

    Args:
        user_id: User ID
        new_rank: New rank
        leaderboard_type: Type of leaderboard
        storage: Storage backend
    """
    notification = {
        'type': 'leaderboard_rank_up',
        'title': '📈 Leaderboard Rank Up!',
        'message': f'You climbed to rank #{new_rank} in {leaderboard_type} leaderboard',
        'icon': '📈',
        'data': {
            'new_rank': new_rank,
            'leaderboard_type': leaderboard_type,
        },
        'priority': 'normal',
        'action_url': '/game/leaderboard',
        'action_text': 'View Leaderboard',
    }

    _send_notification(user_id, notification, storage)


def send_xp_milestone_notification(
    user_id: str,
    total_xp: int,
    milestone: int,
    storage,
):
    """
    Send XP milestone notification.

    Args:
        user_id: User ID
        total_xp: Total XP
        milestone: Milestone reached (e.g., 10000, 50000)
        storage: Storage backend
    """
    notification = {
        'type': 'xp_milestone',
        'title': '⭐ XP Milestone!',
        'message': f'Congratulations! You reached {milestone:,} total XP',
        'icon': '⭐',
        'data': {
            'total_xp': total_xp,
            'milestone': milestone,
        },
        'priority': 'normal',
        'show_celebration': True,
        'celebration_type': 'sparkles',
    }

    _send_notification(user_id, notification, storage)


def _send_notification(
    user_id: str,
    notification: dict,
    storage,
):
    """
    Send notification to user via configured channels.

    Args:
        user_id: User ID
        notification: Notification data
        storage: Storage backend
    """
    # Get user preferences
    user = storage.get_user(user_id)
    if not user:
        return

    # Add timestamp
    notification['timestamp'] = datetime.utcnow().isoformat()
    notification['user_id'] = user_id

    # Save to notification history
    storage.save_notification(notification)

    # Send via configured channels
    # In-app notification (always)
    _send_in_app_notification(user_id, notification, storage)

    # Push notification (if enabled)
    if user.preferences.get('push_notifications', True):
        _send_push_notification(user_id, notification, storage)

    # Email notification (for high priority only)
    if (notification.get('priority') == 'high' and
        user.preferences.get('email_notifications', False)):
        _send_email_notification(user_id, notification, storage)


def _send_in_app_notification(user_id: str, notification: dict, storage):
    """Send in-app notification."""
    # Store in user's notification inbox
    storage.add_to_notification_inbox(user_id, notification)


def _send_push_notification(user_id: str, notification: dict, storage):
    """Send push notification via FCM/APNS."""
    try:
        from src.notifications.push import FirebasePush
        import asyncio

        # Get user's push tokens
        user = storage.get_user(user_id)
        if not user or not hasattr(user, 'preferences'):
            logger.warning(f"User {user_id} not found or has no preferences")
            return

        push_tokens = user.preferences.get('push_tokens', {})
        fcm_tokens = push_tokens.get('fcm', [])

        if not fcm_tokens:
            logger.debug(f"No FCM tokens for user {user_id}")
            return

        # Create push notification
        push_service = FirebasePush()

        # Extract notification data
        title = notification.get('title', 'Notification')
        body = notification.get('message', '')
        data = notification.get('data', {})
        icon = notification.get('icon')

        # Send to all tokens
        async def send_notifications():
            results = await push_service.send_multicast(
                tokens=fcm_tokens,
                title=title,
                body=body,
                data=data,
            )
            success_count = sum(1 for r in results if r.success)
            logger.info(f"Push notification sent to {success_count}/{len(fcm_tokens)} devices for user {user_id}")

        # Schedule async task
        asyncio.create_task(send_notifications())

    except Exception as e:
        logger.error(f"Failed to send push notification: {e}")
        # Fallback to console log for debugging
        print(f"[PUSH] {user_id}: {notification['title']}")


def _send_email_notification(user_id: str, notification: dict, storage):
    """Send email notification."""
    try:
        from src.notifications.email import SendGridEmail
        import asyncio

        # Get user email
        user = storage.get_user(user_id)
        if not user:
            logger.warning(f"User {user_id} not found")
            return

        # Create email content
        email_service = SendGridEmail()
        title = notification.get('title', 'Notification')
        message = notification.get('message', '')

        # Build simple HTML email
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #0066CC; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 30px; background-color: #f9f9f9; }}
        .icon {{ font-size: 48px; text-align: center; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>DocAssist Notification</h1>
        </div>
        <div class="content">
            <div class="icon">{notification.get('icon', '🎉')}</div>
            <h2>{title}</h2>
            <p>{message}</p>
        </div>
    </div>
</body>
</html>
"""

        # Send email asynchronously
        async def send_email():
            result = await email_service.send(
                to=user.email,
                subject=title,
                body=message,
                html_body=html_body,
            )
            if result.success:
                logger.info(f"Email notification sent to {user.email}")
            else:
                logger.error(f"Failed to send email notification: {result.error}")

        # Schedule async task
        asyncio.create_task(send_email())

    except Exception as e:
        logger.error(f"Failed to send email notification: {e}")
        # Fallback to console log for debugging
        print(f"[EMAIL] {user_id}: {notification['title']}")


def get_celebration_animation(celebration_type: str) -> dict:
    """
    Get celebration animation configuration.

    Args:
        celebration_type: Type of celebration

    Returns:
        dict: Animation configuration
    """
    animations = {
        'confetti': {
            'type': 'confetti',
            'duration': 3000,
            'colors': ['#FFD700', '#FF6B6B', '#4ECDC4', '#95E1D3'],
            'particle_count': 150,
        },
        'fireworks': {
            'type': 'fireworks',
            'duration': 4000,
            'colors': ['#FF6B6B', '#FFD93D', '#6BCF7F'],
            'burst_count': 5,
        },
        'badge_reveal': {
            'type': 'badge_reveal',
            'duration': 2000,
            'glow_color': '#FFD700',
            'scale_up': True,
        },
        'stars': {
            'type': 'stars',
            'duration': 2500,
            'colors': ['#FFD700', '#FFA500'],
            'particle_count': 50,
        },
        'sparkles': {
            'type': 'sparkles',
            'duration': 2000,
            'colors': ['#FFFFFF', '#FFD700'],
            'particle_count': 100,
        },
    }

    return animations.get(celebration_type, animations['confetti'])
