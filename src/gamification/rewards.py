"""
Reward System

Redeemable rewards that users can claim with XP or achievements.
"""

from datetime import date, datetime, timedelta
from typing import Optional

from .models import (
    Reward,
    RewardType,
    RewardStatus,
    UserReward,
)


# Pre-defined reward catalog
REWARD_CATALOG = [
    {
        'reward_type': RewardType.SUBSCRIPTION_DISCOUNT,
        'title': '10% Subscription Discount',
        'description': '10% off your next month subscription',
        'icon': '💰',
        'xp_cost': 1000,
        'level_required': 10,
        'monetary_value': 99.0,
        'total_quantity': None,  # Unlimited
    },
    {
        'reward_type': RewardType.SUBSCRIPTION_DISCOUNT,
        'title': '25% Subscription Discount',
        'description': '25% off your next month subscription',
        'icon': '💎',
        'xp_cost': 3000,
        'level_required': 25,
        'monetary_value': 247.5,
        'total_quantity': None,
    },
    {
        'reward_type': RewardType.SUBSCRIPTION_DISCOUNT,
        'title': '1 Month Free Subscription',
        'description': 'Get 1 month subscription for free',
        'icon': '🎁',
        'xp_cost': 10000,
        'level_required': 50,
        'monetary_value': 999.0,
        'total_quantity': 100,
    },
    {
        'reward_type': RewardType.PREMIUM_FEATURE,
        'title': 'Voice Query Premium (1 Month)',
        'description': 'Unlock advanced voice query features for 1 month',
        'icon': '🎤',
        'xp_cost': 2500,
        'level_required': 20,
        'monetary_value': 299.0,
        'total_quantity': None,
    },
    {
        'reward_type': RewardType.PREMIUM_FEATURE,
        'title': 'Priority Support (1 Month)',
        'description': 'Get priority customer support for 1 month',
        'icon': '⚡',
        'xp_cost': 5000,
        'level_required': 30,
        'monetary_value': 499.0,
        'total_quantity': None,
    },
    {
        'reward_type': RewardType.CME_COURSE,
        'title': 'Free CME Course Access',
        'description': 'Access to any premium CME course',
        'icon': '🎓',
        'xp_cost': 7500,
        'level_required': 40,
        'monetary_value': 1999.0,
        'total_quantity': 50,
    },
    {
        'reward_type': RewardType.CONFERENCE_TICKET,
        'title': 'Virtual Conference Ticket',
        'description': 'Free ticket to upcoming medical virtual conference',
        'icon': '🎫',
        'xp_cost': 15000,
        'level_required': 60,
        'monetary_value': 4999.0,
        'total_quantity': 20,
        'partner': 'MedConf India',
    },
    {
        'reward_type': RewardType.MEDICAL_BOOK,
        'title': 'Medical Textbook (Digital)',
        'description': 'Choose any digital medical textbook from our library',
        'icon': '📚',
        'xp_cost': 5000,
        'level_required': 35,
        'monetary_value': 2999.0,
        'total_quantity': None,
    },
    {
        'reward_type': RewardType.GIFT_CARD,
        'title': '₹500 Amazon Gift Card',
        'description': 'Amazon India gift card worth ₹500',
        'icon': '🛍️',
        'xp_cost': 12000,
        'level_required': 50,
        'monetary_value': 500.0,
        'total_quantity': 30,
    },
    {
        'reward_type': RewardType.GIFT_CARD,
        'title': '₹1000 Amazon Gift Card',
        'description': 'Amazon India gift card worth ₹1000',
        'icon': '🛍️',
        'xp_cost': 20000,
        'level_required': 70,
        'monetary_value': 1000.0,
        'total_quantity': 15,
    },
]


class RewardService:
    """Service for managing rewards"""

    def __init__(self, storage):
        """
        Initialize reward service.

        Args:
            storage: Storage backend
        """
        self.storage = storage
        self._initialize_rewards()

    def _initialize_rewards(self):
        """Initialize reward catalog in storage."""
        for reward_def in REWARD_CATALOG:
            # Check if reward exists
            existing = self.storage.get_reward_by_title(reward_def['title'])
            if not existing:
                # Create new reward
                reward = Reward(
                    **reward_def,
                    remaining_quantity=reward_def['total_quantity'],
                )
                self.storage.save_reward(reward)

    def get_available_rewards(
        self,
        user_id: str,
        reward_type: Optional[RewardType] = None,
    ) -> list[dict]:
        """
        Get rewards available to user.

        Args:
            user_id: User ID
            reward_type: Filter by type (optional)

        Returns:
            list[dict]: Available rewards with affordability info
        """
        # Get user progress
        progress = self.storage.get_user_progress(user_id)
        if not progress:
            return []

        # Get all active rewards
        all_rewards = self.storage.get_active_rewards(reward_type)

        # Filter and annotate rewards
        available = []
        for reward in all_rewards:
            # Check if in stock
            if reward.remaining_quantity is not None and reward.remaining_quantity <= 0:
                continue

            # Check level requirement
            meets_level = progress.current_level >= reward.level_required

            # Check XP cost
            can_afford = progress.total_xp >= reward.xp_cost

            # Check badge requirements
            meets_badge_req = True
            for badge_key in reward.required_badges:
                if not self.storage.get_user_badge_by_key(user_id, badge_key):
                    meets_badge_req = False
                    break

            # Determine status
            if meets_level and can_afford and meets_badge_req:
                status = RewardStatus.AVAILABLE
            else:
                status = RewardStatus.LOCKED

            available.append({
                'reward': reward,
                'status': status,
                'meets_level': meets_level,
                'can_afford': can_afford,
                'meets_badge_req': meets_badge_req,
                'xp_needed': max(0, reward.xp_cost - progress.total_xp),
                'levels_needed': max(0, reward.level_required - progress.current_level),
            })

        return available

    def redeem_reward(
        self,
        user_id: str,
        reward_id: str,
    ) -> dict:
        """
        Redeem a reward.

        Args:
            user_id: User ID
            reward_id: Reward ID

        Returns:
            dict: Redemption result
        """
        # Get reward
        reward = self.storage.get_reward(reward_id)
        if not reward:
            return {
                'success': False,
                'message': 'Reward not found',
            }

        # Check if active
        if not reward.is_active:
            return {
                'success': False,
                'message': 'Reward is no longer available',
            }

        # Check validity
        if reward.valid_until and reward.valid_until < date.today():
            return {
                'success': False,
                'message': 'Reward has expired',
            }

        # Check stock
        if reward.remaining_quantity is not None and reward.remaining_quantity <= 0:
            return {
                'success': False,
                'message': 'Reward is out of stock',
            }

        # Get user progress
        progress = self.storage.get_user_progress(user_id)
        if not progress:
            return {
                'success': False,
                'message': 'User progress not found',
            }

        # Check level requirement
        if progress.current_level < reward.level_required:
            return {
                'success': False,
                'message': f'Requires level {reward.level_required}',
            }

        # Check XP cost
        if progress.total_xp < reward.xp_cost:
            return {
                'success': False,
                'message': f'Insufficient XP (need {reward.xp_cost})',
            }

        # Check badge requirements
        for badge_key in reward.required_badges:
            if not self.storage.get_user_badge_by_key(user_id, badge_key):
                return {
                    'success': False,
                    'message': f'Requires badge: {badge_key}',
                }

        # Redeem reward
        user_reward = UserReward(
            user_id=user_id,
            reward_id=reward_id,
            reward_title=reward.title,
            reward_type=reward.reward_type,
            reward_description=reward.description,
            xp_spent=reward.xp_cost,
            status=RewardStatus.REDEEMED,
            instructions=self._generate_instructions(reward),
        )

        # Set expiration (30 days for most rewards)
        user_reward.expires_at = datetime.utcnow() + timedelta(days=30)

        # Save user reward
        self.storage.save_user_reward(user_reward)

        # Deduct XP (optional - or keep it as achievement)
        # For now, we don't deduct - XP is cumulative

        # Decrement stock
        if reward.remaining_quantity is not None:
            reward.remaining_quantity -= 1
            reward.total_redemptions += 1
            self.storage.save_reward(reward)

        # Send notification
        from .notifications import send_reward_redeemed_notification
        send_reward_redeemed_notification(user_id, user_reward, self.storage)

        return {
            'success': True,
            'message': 'Reward redeemed successfully!',
            'user_reward': user_reward,
            'redemption_code': user_reward.redemption_code,
            'instructions': user_reward.instructions,
        }

    def get_user_rewards(
        self,
        user_id: str,
        status: Optional[RewardStatus] = None,
    ) -> list[UserReward]:
        """
        Get user's redeemed rewards.

        Args:
            user_id: User ID
            status: Filter by status (optional)

        Returns:
            list[UserReward]: User's rewards
        """
        return self.storage.get_user_rewards(user_id, status)

    def mark_reward_fulfilled(
        self,
        user_reward_id: str,
        fulfillment_notes: Optional[str] = None,
    ) -> dict:
        """
        Mark a reward as fulfilled.

        Args:
            user_reward_id: User reward ID
            fulfillment_notes: Notes about fulfillment

        Returns:
            dict: Result
        """
        user_reward = self.storage.get_user_reward_by_id(user_reward_id)
        if not user_reward:
            return {
                'success': False,
                'message': 'Reward not found',
            }

        user_reward.fulfilled = True
        user_reward.fulfilled_at = datetime.utcnow()
        user_reward.fulfillment_notes = fulfillment_notes

        self.storage.save_user_reward(user_reward)

        return {
            'success': True,
            'message': 'Reward marked as fulfilled',
        }

    def _generate_instructions(self, reward: Reward) -> str:
        """Generate redemption instructions for a reward."""
        instructions_map = {
            RewardType.SUBSCRIPTION_DISCOUNT: (
                "Your discount code is ready! Apply code '{code}' at checkout. "
                "Valid for 30 days from redemption."
            ),
            RewardType.PREMIUM_FEATURE: (
                "Premium feature unlocked! Access it from your dashboard. "
                "Enjoy enhanced features for the next month."
            ),
            RewardType.CME_COURSE: (
                "Your CME course access code: {code}. "
                "Visit our learning portal and enter this code to enroll."
            ),
            RewardType.CONFERENCE_TICKET: (
                "Congratulations! Your conference ticket code: {code}. "
                "Check your email for registration details."
            ),
            RewardType.MEDICAL_BOOK: (
                "Book voucher code: {code}. "
                "Visit our library and use this code to download your chosen textbook."
            ),
            RewardType.GIFT_CARD: (
                "Your gift card code: {code}. "
                "Redeem on Amazon India within 30 days."
            ),
        }

        template = instructions_map.get(
            reward.reward_type,
            "Your reward code: {code}. Check your email for details."
        )

        return template

    def get_reward_statistics(self) -> dict:
        """Get overall reward statistics."""
        total_rewards = len(self.storage.get_all_rewards())
        total_redemptions = self.storage.count_total_redemptions()
        most_popular = self.storage.get_most_redeemed_rewards(limit=5)

        return {
            'total_rewards': total_rewards,
            'total_redemptions': total_redemptions,
            'most_popular': most_popular,
        }
