"""
CME Credit Management System

Handles CME credit calculation, tracking, and compliance with MCI and state medical council requirements.
"""

from datetime import date, datetime, timedelta
from typing import Optional
import logging

from .models import (
    LearningActivity,
    CMECredit,
    ActivityType,
    CMECategory,
    AccreditationBody,
)

logger = logging.getLogger(__name__)


class CMECreditSystem:
    """Manages CME credits and compliance"""

    # Credit rules per activity type
    ACTIVITY_CREDIT_RULES = {
        ActivityType.QUERY: {
            "max_credits": 0.05,
            "category": CMECategory.CATEGORY_2,
            "requires_duration": 60,  # seconds
        },
        ActivityType.QUERY_DEEP: {
            "max_credits": 0.1,
            "category": CMECategory.CATEGORY_2,
            "requires_duration": 120,  # seconds
        },
        ActivityType.CALCULATOR: {
            "max_credits": 0.05,
            "category": CMECategory.CATEGORY_2,
            "requires_duration": 30,
        },
        ActivityType.ARTICLE_READ: {
            "max_credits": 0.25,
            "category": CMECategory.CATEGORY_2,
            "requires_completion": 70,  # percentage
        },
        ActivityType.VIDEO_VIEW: {
            "max_credits": 0.5,
            "category": CMECategory.CATEGORY_1,
            "requires_completion": 80,  # percentage
        },
        ActivityType.QUIZ_PASS: {
            "max_credits": 0.5,
            "category": CMECategory.CATEGORY_1,
            "requires_passing": True,
        },
        ActivityType.CASE_STUDY: {
            "max_credits": 1.0,
            "category": CMECategory.CATEGORY_1,
            "requires_completion": True,
        },
        ActivityType.MODULE_COMPLETE: {
            "max_credits": 2.0,
            "category": CMECategory.CATEGORY_1,
            "requires_completion": True,
        },
        ActivityType.PATH_COMPLETE: {
            "max_credits": 10.0,
            "category": CMECategory.CATEGORY_1,
            "requires_completion": True,
        },
    }

    # Limits
    MAX_CREDITS_PER_DAY = 2.0
    MAX_CREDITS_PER_WEEK = 10.0
    MAX_CREDITS_PER_ACTIVITY_TYPE_PER_DAY = {
        ActivityType.QUERY: 0.5,
        ActivityType.QUERY_DEEP: 1.0,
        ActivityType.CALCULATOR: 0.2,
    }

    # MCI annual requirements
    ANNUAL_REQUIREMENT_MCI = 30.0  # 30 credits per year
    CREDIT_VALIDITY_YEARS = 5

    def __init__(self):
        self.credits: list[CMECredit] = []

    def award_credit_for_activity(
        self,
        activity: LearningActivity,
        accreditation_body: AccreditationBody = AccreditationBody.SELF_DIRECTED,
    ) -> Optional[CMECredit]:
        """
        Award CME credit for a learning activity

        Args:
            activity: The learning activity
            accreditation_body: Accreditation body

        Returns:
            CMECredit if awarded, None otherwise
        """
        # Check if activity qualifies for credits
        if not self._qualifies_for_credit(activity):
            logger.info(f"Activity {activity.id} does not qualify for CME credit")
            return None

        # Check daily limits
        if not self._check_daily_limits(activity.user_id, activity.activity_type):
            logger.warning(f"User {activity.user_id} has reached daily limit for {activity.activity_type}")
            return None

        # Calculate credits
        credits_amount = self._calculate_credits(activity)
        if credits_amount == 0:
            return None

        # Determine category
        category = self._get_activity_category(activity.activity_type)

        # Create credit record
        credit = CMECredit(
            user_id=activity.user_id,
            activity_id=activity.id,
            credits=credits_amount,
            category=category,
            accreditation_body=accreditation_body,
            activity_title=activity.title,
            activity_type=activity.activity_type,
            specialty=activity.specialty,
            topics=activity.topics,
            earned_date=date.today(),
            expires_date=date.today() + timedelta(days=365 * self.CREDIT_VALIDITY_YEARS),
            is_valid=True,
        )

        self.credits.append(credit)
        logger.info(
            f"Awarded {credits_amount} CME credits to user {activity.user_id} "
            f"for activity {activity.activity_type}"
        )

        return credit

    def get_user_credits(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category: Optional[CMECategory] = None,
        only_valid: bool = True,
    ) -> list[CMECredit]:
        """
        Get user's CME credits

        Args:
            user_id: User ID
            start_date: Filter by start date
            end_date: Filter by end date
            category: Filter by category
            only_valid: Only include valid (non-expired) credits

        Returns:
            List of CME credits
        """
        credits = [c for c in self.credits if c.user_id == user_id]

        if start_date:
            credits = [c for c in credits if c.earned_date >= start_date]

        if end_date:
            credits = [c for c in credits if c.earned_date <= end_date]

        if category:
            credits = [c for c in credits if c.category == category]

        if only_valid:
            today = date.today()
            credits = [c for c in credits if c.is_valid and c.expires_date >= today]

        return sorted(credits, key=lambda x: x.earned_date, reverse=True)

    def get_total_credits(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category: Optional[CMECategory] = None,
    ) -> float:
        """
        Get total CME credits for a user

        Args:
            user_id: User ID
            start_date: Start date
            end_date: End date
            category: Filter by category

        Returns:
            Total credits
        """
        credits = self.get_user_credits(user_id, start_date, end_date, category)
        return sum(c.credits for c in credits)

    def get_annual_credits(self, user_id: str, year: Optional[int] = None) -> dict[str, float]:
        """
        Get annual CME credits summary

        Args:
            user_id: User ID
            year: Year (default: current year)

        Returns:
            Dict with credit breakdown
        """
        if year is None:
            year = date.today().year

        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

        total = self.get_total_credits(user_id, start_date, end_date)

        # By category
        category_1 = self.get_total_credits(user_id, start_date, end_date, CMECategory.CATEGORY_1)
        category_2 = self.get_total_credits(user_id, start_date, end_date, CMECategory.CATEGORY_2)
        category_3 = self.get_total_credits(user_id, start_date, end_date, CMECategory.CATEGORY_3)

        # Progress toward annual requirement
        progress_percentage = min(100.0, (total / self.ANNUAL_REQUIREMENT_MCI) * 100)

        return {
            "year": year,
            "total_credits": total,
            "category_1_credits": category_1,
            "category_2_credits": category_2,
            "category_3_credits": category_3,
            "annual_requirement": self.ANNUAL_REQUIREMENT_MCI,
            "progress_percentage": progress_percentage,
            "credits_remaining": max(0, self.ANNUAL_REQUIREMENT_MCI - total),
            "requirement_met": total >= self.ANNUAL_REQUIREMENT_MCI,
        }

    def get_credits_by_specialty(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict[str, float]:
        """
        Get credits grouped by specialty

        Args:
            user_id: User ID
            start_date: Start date
            end_date: End date

        Returns:
            Dict of specialty -> credits
        """
        credits = self.get_user_credits(user_id, start_date, end_date)

        specialty_credits: dict[str, float] = {}
        for credit in credits:
            if credit.specialty:
                specialty_credits[credit.specialty] = (
                    specialty_credits.get(credit.specialty, 0.0) + credit.credits
                )

        return specialty_credits

    def get_credits_by_topic(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict[str, float]:
        """
        Get credits grouped by topic

        Args:
            user_id: User ID
            start_date: Start date
            end_date: End date

        Returns:
            Dict of topic -> credits
        """
        credits = self.get_user_credits(user_id, start_date, end_date)

        topic_credits: dict[str, float] = {}
        for credit in credits:
            for topic in credit.topics:
                topic_credits[topic] = topic_credits.get(topic, 0.0) + credit.credits

        return topic_credits

    def get_expiring_credits(
        self,
        user_id: str,
        days_until_expiry: int = 90,
    ) -> list[CMECredit]:
        """
        Get credits expiring soon

        Args:
            user_id: User ID
            days_until_expiry: Days threshold

        Returns:
            List of expiring credits
        """
        cutoff_date = date.today() + timedelta(days=days_until_expiry)
        credits = self.get_user_credits(user_id, only_valid=True)

        expiring = [
            c for c in credits
            if c.expires_date <= cutoff_date
        ]

        return sorted(expiring, key=lambda x: x.expires_date)

    def verify_credit(self, verification_code: str) -> Optional[CMECredit]:
        """
        Verify a CME credit by verification code

        Args:
            verification_code: Verification code

        Returns:
            CMECredit if found, None otherwise
        """
        for credit in self.credits:
            if credit.verification_code == verification_code.upper():
                return credit

        return None

    def invalidate_credit(self, credit_id: str, reason: str = "") -> bool:
        """
        Invalidate a credit (e.g., if activity was fraudulent)

        Args:
            credit_id: Credit ID
            reason: Reason for invalidation

        Returns:
            True if invalidated, False if not found
        """
        for credit in self.credits:
            if credit.id == credit_id:
                credit.is_valid = False
                credit.metadata["invalidation_reason"] = reason
                credit.metadata["invalidated_at"] = datetime.utcnow().isoformat()
                logger.warning(f"Invalidated credit {credit_id}: {reason}")
                return True

        return False

    def transfer_credits(
        self,
        from_user_id: str,
        to_user_id: str,
        credit_ids: list[str],
    ) -> int:
        """
        Transfer credits between users (e.g., during account merge)

        Args:
            from_user_id: Source user ID
            to_user_id: Destination user ID
            credit_ids: List of credit IDs to transfer

        Returns:
            Number of credits transferred
        """
        transferred = 0

        for credit in self.credits:
            if credit.id in credit_ids and credit.user_id == from_user_id:
                credit.user_id = to_user_id
                credit.metadata["transferred_from"] = from_user_id
                credit.metadata["transferred_at"] = datetime.utcnow().isoformat()
                transferred += 1
                logger.info(f"Transferred credit {credit.id} from {from_user_id} to {to_user_id}")

        return transferred

    def _qualifies_for_credit(self, activity: LearningActivity) -> bool:
        """
        Check if activity qualifies for CME credit

        Args:
            activity: Learning activity

        Returns:
            True if qualifies
        """
        # Must be completed
        if activity.completed_at is None:
            return False

        # Check activity-specific rules
        rules = self.ACTIVITY_CREDIT_RULES.get(activity.activity_type)
        if not rules:
            return False

        # Check duration requirement
        if "requires_duration" in rules:
            if activity.duration_seconds < rules["requires_duration"]:
                return False

        # Check completion requirement (stored in metadata)
        if "requires_completion" in rules:
            completion = activity.metadata.get("completion_percentage", 0)
            if completion < rules["requires_completion"]:
                return False

        # Check passing requirement
        if rules.get("requires_passing") and not activity.metadata.get("passed"):
            return False

        return True

    def _calculate_credits(self, activity: LearningActivity) -> float:
        """
        Calculate credit amount for activity

        Args:
            activity: Learning activity

        Returns:
            Credit amount
        """
        rules = self.ACTIVITY_CREDIT_RULES.get(activity.activity_type)
        if not rules:
            return 0.0

        # Use pre-calculated credits from activity, capped by max
        max_credits = rules.get("max_credits", 0.0)
        return min(activity.cme_credits_earned, max_credits)

    def _get_activity_category(self, activity_type: ActivityType) -> CMECategory:
        """
        Get CME category for activity type

        Args:
            activity_type: Activity type

        Returns:
            CME category
        """
        rules = self.ACTIVITY_CREDIT_RULES.get(activity_type, {})
        return rules.get("category", CMECategory.CATEGORY_2)

    def _check_daily_limits(self, user_id: str, activity_type: ActivityType) -> bool:
        """
        Check if user has exceeded daily limits

        Args:
            user_id: User ID
            activity_type: Activity type

        Returns:
            True if within limits
        """
        today = date.today()
        today_credits = self.get_user_credits(
            user_id,
            start_date=today,
            end_date=today,
        )

        # Check total daily limit
        total_today = sum(c.credits for c in today_credits)
        if total_today >= self.MAX_CREDITS_PER_DAY:
            return False

        # Check per-activity-type limit
        type_limit = self.MAX_CREDITS_PER_ACTIVITY_TYPE_PER_DAY.get(activity_type)
        if type_limit:
            type_credits_today = sum(
                c.credits for c in today_credits
                if c.activity_type == activity_type
            )
            if type_credits_today >= type_limit:
                return False

        return True


# Global CME system instance
_cme_system = CMECreditSystem()


def get_cme_system() -> CMECreditSystem:
    """Get the global CME system instance"""
    return _cme_system
