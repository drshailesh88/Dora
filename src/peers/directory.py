"""
Specialist Directory

Find and browse verified specialists by specialty, location, ratings, etc.
"""

from datetime import datetime
from typing import Any, Optional

from src.peers.models import (
    Specialist,
    VerificationLevel,
    Expertise,
    ConsultFee,
    Availability,
)


class SpecialistDirectory:
    """Manages specialist directory and search."""

    def __init__(self):
        """Initialize directory."""
        # In production, this would use database
        self.specialists: dict[str, Specialist] = {}
        self.fees: dict[str, list[ConsultFee]] = {}
        self.availability: dict[str, list[Availability]] = {}

    def register_specialist(
        self,
        user_id: str,
        name: str,
        email: str,
        registration_number: str,
        primary_specialty: str,
        **kwargs,
    ) -> Specialist:
        """
        Register a new specialist.

        Args:
            user_id: User ID
            name: Full name
            email: Email address
            registration_number: Medical license number
            primary_specialty: Primary specialty
            **kwargs: Additional profile fields

        Returns:
            Specialist profile
        """
        specialist = Specialist(
            user_id=user_id,
            name=name,
            email=email,
            registration_number=registration_number,
            primary_specialty=primary_specialty,
            **kwargs,
        )

        self.specialists[specialist.id] = specialist
        return specialist

    def get_specialist(self, specialist_id: str) -> Optional[Specialist]:
        """
        Get specialist by ID.

        Args:
            specialist_id: Specialist ID

        Returns:
            Specialist or None
        """
        return self.specialists.get(specialist_id)

    def update_specialist(
        self,
        specialist_id: str,
        **updates,
    ) -> Optional[Specialist]:
        """
        Update specialist profile.

        Args:
            specialist_id: Specialist ID
            **updates: Fields to update

        Returns:
            Updated specialist or None
        """
        specialist = self.specialists.get(specialist_id)
        if not specialist:
            return None

        for key, value in updates.items():
            if hasattr(specialist, key):
                setattr(specialist, key, value)

        specialist.updated_at = datetime.utcnow()
        return specialist

    def search_specialists(
        self,
        specialty: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        verification_level: Optional[VerificationLevel] = None,
        min_rating: float = 0.0,
        is_available: bool = False,
        language: Optional[str] = None,
        max_fee: Optional[int] = None,
        limit: int = 20,
    ) -> list[Specialist]:
        """
        Search specialists with filters.

        Args:
            specialty: Filter by specialty
            city: Filter by city
            state: Filter by state
            verification_level: Minimum verification level
            min_rating: Minimum average rating
            is_available: Only accepting consults
            language: Language spoken
            max_fee: Maximum consultation fee
            limit: Maximum results

        Returns:
            List of matching specialists
        """
        results = []

        for specialist in self.specialists.values():
            # Apply filters
            if specialty and specialist.primary_specialty != specialty:
                continue

            if city and specialist.city.lower() != city.lower():
                continue

            if state and specialist.state.lower() != state.lower():
                continue

            if verification_level:
                # Check if verification level is sufficient
                level_order = {
                    VerificationLevel.UNVERIFIED: 0,
                    VerificationLevel.VERIFIED: 1,
                    VerificationLevel.CERTIFIED: 2,
                    VerificationLevel.EXPERT: 3,
                }
                if level_order.get(specialist.verification_level, 0) < level_order.get(verification_level, 0):
                    continue

            if specialist.average_rating < min_rating:
                continue

            if is_available and not specialist.is_accepting_consults:
                continue

            if language and language not in specialist.languages:
                continue

            if max_fee:
                # Check if any fee is within budget
                specialist_fees = self.fees.get(specialist.id, [])
                if specialist_fees and all(fee.fee_amount > max_fee for fee in specialist_fees):
                    continue

            results.append(specialist)

        # Sort by rating and total consultations
        results.sort(
            key=lambda s: (s.average_rating, s.total_consultations),
            reverse=True,
        )

        return results[:limit]

    def get_specialists_by_specialty(
        self,
        specialty: str,
        limit: int = 20,
    ) -> list[Specialist]:
        """
        Get top specialists for a specialty.

        Args:
            specialty: Specialty name
            limit: Maximum results

        Returns:
            List of specialists
        """
        return self.search_specialists(
            specialty=specialty,
            verification_level=VerificationLevel.VERIFIED,
            is_available=True,
            limit=limit,
        )

    def get_featured_specialists(self, limit: int = 10) -> list[Specialist]:
        """
        Get featured/top specialists.

        Args:
            limit: Maximum results

        Returns:
            List of top specialists
        """
        featured = [
            s for s in self.specialists.values()
            if s.verification_level in [VerificationLevel.CERTIFIED, VerificationLevel.EXPERT]
            and s.average_rating >= 4.5
            and s.total_consultations >= 20
        ]

        featured.sort(
            key=lambda s: (s.average_rating, s.total_consultations),
            reverse=True,
        )

        return featured[:limit]

    def add_expertise(
        self,
        specialist_id: str,
        expertise: Expertise,
    ) -> bool:
        """
        Add expertise area to specialist.

        Args:
            specialist_id: Specialist ID
            expertise: Expertise to add

        Returns:
            Success status
        """
        specialist = self.specialists.get(specialist_id)
        if not specialist:
            return False

        specialist.expertise.append(expertise)
        specialist.updated_at = datetime.utcnow()
        return True

    def set_fees(
        self,
        specialist_id: str,
        fees: list[ConsultFee],
    ) -> bool:
        """
        Set consultation fees for specialist.

        Args:
            specialist_id: Specialist ID
            fees: List of consultation fees

        Returns:
            Success status
        """
        if specialist_id not in self.specialists:
            return False

        self.fees[specialist_id] = fees
        return True

    def get_fees(self, specialist_id: str) -> list[ConsultFee]:
        """
        Get consultation fees for specialist.

        Args:
            specialist_id: Specialist ID

        Returns:
            List of fees
        """
        return self.fees.get(specialist_id, [])

    def set_availability(
        self,
        specialist_id: str,
        availability: list[Availability],
    ) -> bool:
        """
        Set availability schedule for specialist.

        Args:
            specialist_id: Specialist ID
            availability: List of availability slots

        Returns:
            Success status
        """
        if specialist_id not in self.specialists:
            return False

        self.availability[specialist_id] = availability
        return True

    def get_availability(self, specialist_id: str) -> list[Availability]:
        """
        Get availability schedule for specialist.

        Args:
            specialist_id: Specialist ID

        Returns:
            List of availability slots
        """
        return self.availability.get(specialist_id, [])

    def is_specialist_available_now(self, specialist_id: str) -> bool:
        """
        Check if specialist is available right now.

        Args:
            specialist_id: Specialist ID

        Returns:
            True if available
        """
        specialist = self.specialists.get(specialist_id)
        if not specialist or not specialist.is_accepting_consults:
            return False

        # Check availability schedule
        availability_slots = self.availability.get(specialist_id, [])
        if not availability_slots:
            return True  # No schedule means always available

        now = datetime.utcnow()
        day_of_week = now.weekday()

        for slot in availability_slots:
            if slot.day_of_week == day_of_week and slot.is_available():
                # TODO: Check time range
                return True

        return False

    def update_stats(
        self,
        specialist_id: str,
        rating: Optional[float] = None,
        response_time_hours: Optional[float] = None,
        accepted_consult: bool = False,
        declined_consult: bool = False,
    ) -> bool:
        """
        Update specialist statistics.

        Args:
            specialist_id: Specialist ID
            rating: New rating to incorporate
            response_time_hours: Response time to incorporate
            accepted_consult: Increment acceptance count
            declined_consult: Increment decline count

        Returns:
            Success status
        """
        specialist = self.specialists.get(specialist_id)
        if not specialist:
            return False

        # Update rating
        if rating is not None:
            total_ratings = specialist.total_reviews
            current_avg = specialist.average_rating

            new_total = total_ratings + 1
            new_avg = ((current_avg * total_ratings) + rating) / new_total

            specialist.average_rating = new_avg
            specialist.total_reviews = new_total

        # Update response time
        if response_time_hours is not None:
            total_consults = specialist.total_consultations or 1
            current_avg = specialist.average_response_time_hours

            new_avg = ((current_avg * total_consults) + response_time_hours) / (total_consults + 1)
            specialist.average_response_time_hours = new_avg

        # Update acceptance rate
        if accepted_consult or declined_consult:
            # This is simplified - in production, track separately
            specialist.total_consultations += 1 if accepted_consult else 0

        specialist.updated_at = datetime.utcnow()
        return True

    def get_specialist_by_user_id(self, user_id: str) -> Optional[Specialist]:
        """
        Get specialist by user ID.

        Args:
            user_id: User ID

        Returns:
            Specialist or None
        """
        for specialist in self.specialists.values():
            if specialist.user_id == user_id:
                return specialist
        return None

    def get_directory_stats(self) -> dict[str, Any]:
        """
        Get directory statistics.

        Returns:
            Statistics dictionary
        """
        total = len(self.specialists)
        by_specialty: dict[str, int] = {}
        by_verification: dict[str, int] = {}
        by_city: dict[str, int] = {}

        for specialist in self.specialists.values():
            # Count by specialty
            specialty = specialist.primary_specialty
            by_specialty[specialty] = by_specialty.get(specialty, 0) + 1

            # Count by verification level
            level = specialist.verification_level.value
            by_verification[level] = by_verification.get(level, 0) + 1

            # Count by city
            city = specialist.city
            if city:
                by_city[city] = by_city.get(city, 0) + 1

        return {
            "total_specialists": total,
            "by_specialty": by_specialty,
            "by_verification_level": by_verification,
            "by_city": by_city,
            "average_rating": sum(s.average_rating for s in self.specialists.values()) / total if total > 0 else 0.0,
            "total_consultations": sum(s.total_consultations for s in self.specialists.values()),
        }
