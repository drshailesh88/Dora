"""
Smart Matching Engine

Intelligently match consultation requests with best-suited specialists.
"""

from datetime import datetime
from typing import Any, Optional

from src.peers.models import (
    ConsultRequest,
    Specialist,
    VerificationLevel,
    ConsultPriority,
)


class SpecialistMatcher:
    """Matches consultation requests to optimal specialists."""

    def __init__(self):
        """Initialize matcher."""
        pass

    def find_best_match(
        self,
        request: ConsultRequest,
        available_specialists: list[Specialist],
        consider_availability: bool = True,
        consider_fee: bool = True,
        consider_language: bool = True,
    ) -> Optional[Specialist]:
        """
        Find the best specialist match for a consultation request.

        Args:
            request: Consultation request
            available_specialists: List of available specialists
            consider_availability: Consider specialist availability
            consider_fee: Consider fee constraints
            consider_language: Consider language preference

        Returns:
            Best matched specialist or None
        """
        if not available_specialists:
            return None

        # Filter specialists
        candidates = self._filter_candidates(
            request=request,
            specialists=available_specialists,
            consider_availability=consider_availability,
            consider_fee=consider_fee,
            consider_language=consider_language,
        )

        if not candidates:
            return None

        # Score candidates
        scored_candidates = [
            (specialist, self._calculate_match_score(request, specialist))
            for specialist in candidates
        ]

        # Sort by score (highest first)
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        # Return best match
        return scored_candidates[0][0]

    def find_top_matches(
        self,
        request: ConsultRequest,
        available_specialists: list[Specialist],
        limit: int = 5,
    ) -> list[tuple[Specialist, float]]:
        """
        Find top N specialist matches for a consultation request.

        Args:
            request: Consultation request
            available_specialists: List of available specialists
            limit: Maximum number of matches

        Returns:
            List of (specialist, score) tuples
        """
        if not available_specialists:
            return []

        # Filter candidates
        candidates = self._filter_candidates(
            request=request,
            specialists=available_specialists,
        )

        # Score all candidates
        scored_candidates = [
            (specialist, self._calculate_match_score(request, specialist))
            for specialist in candidates
        ]

        # Sort by score (highest first)
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        return scored_candidates[:limit]

    def _filter_candidates(
        self,
        request: ConsultRequest,
        specialists: list[Specialist],
        consider_availability: bool = True,
        consider_fee: bool = True,
        consider_language: bool = True,
    ) -> list[Specialist]:
        """
        Filter specialists based on request requirements.

        Args:
            request: Consultation request
            specialists: List of specialists
            consider_availability: Filter by availability
            consider_fee: Filter by fee
            consider_language: Filter by language

        Returns:
            Filtered list of specialists
        """
        candidates = []

        for specialist in specialists:
            # Must match specialty
            if specialist.primary_specialty != request.specialty_needed:
                continue

            # Must be accepting consults
            if consider_availability and not specialist.is_accepting_consults:
                continue

            # Check verification level (higher priority needs higher verification)
            min_verification = {
                ConsultPriority.ROUTINE: VerificationLevel.VERIFIED,
                ConsultPriority.URGENT: VerificationLevel.CERTIFIED,
                ConsultPriority.EMERGENCY: VerificationLevel.CERTIFIED,
            }
            required_level = min_verification[request.priority]
            level_order = {
                VerificationLevel.UNVERIFIED: 0,
                VerificationLevel.VERIFIED: 1,
                VerificationLevel.CERTIFIED: 2,
                VerificationLevel.EXPERT: 3,
            }
            if level_order[specialist.verification_level] < level_order[required_level]:
                continue

            # Check language preference
            if consider_language and request.preferred_language:
                if request.preferred_language not in specialist.languages:
                    continue

            # Check fee constraints by integrating with fee data
            if consider_fee and request.max_fee:
                # Import directory to access fee data
                from src.peers.directory import SpecialistDirectory
                directory = SpecialistDirectory()

                # Get specialist fees
                fees = directory.get_fees(specialist.id)
                if fees:
                    # Check if any fee option is within the budget
                    affordable_fees = [fee for fee in fees if fee.fee_amount <= request.max_fee]
                    if not affordable_fees:
                        continue  # Skip if all fees exceed max_fee

            candidates.append(specialist)

        return candidates

    def _calculate_match_score(
        self,
        request: ConsultRequest,
        specialist: Specialist,
    ) -> float:
        """
        Calculate match score for specialist-request pair.

        Args:
            request: Consultation request
            specialist: Specialist

        Returns:
            Match score (0-100)
        """
        score = 0.0

        # Specialty match (30 points)
        if specialist.primary_specialty == request.specialty_needed:
            score += 30

        # Verification level (20 points)
        verification_scores = {
            VerificationLevel.UNVERIFIED: 0,
            VerificationLevel.VERIFIED: 10,
            VerificationLevel.CERTIFIED: 15,
            VerificationLevel.EXPERT: 20,
        }
        score += verification_scores[specialist.verification_level]

        # Rating (20 points)
        score += (specialist.average_rating / 5.0) * 20

        # Experience (15 points based on total consultations)
        if specialist.total_consultations >= 100:
            score += 15
        elif specialist.total_consultations >= 50:
            score += 12
        elif specialist.total_consultations >= 20:
            score += 8
        elif specialist.total_consultations >= 5:
            score += 5

        # Response time (10 points - faster is better)
        expected_hours = {
            ConsultPriority.ROUTINE: 24,
            ConsultPriority.URGENT: 6,
            ConsultPriority.EMERGENCY: 1,
        }
        expected = expected_hours[request.priority]
        if specialist.average_response_time_hours <= expected:
            score += 10
        elif specialist.average_response_time_hours <= expected * 2:
            score += 5

        # Language match (5 points)
        if request.preferred_language in specialist.languages:
            score += 5

        return score

    def auto_assign(
        self,
        request: ConsultRequest,
        available_specialists: list[Specialist],
    ) -> Optional[str]:
        """
        Automatically assign best specialist to request.

        Args:
            request: Consultation request
            available_specialists: List of available specialists

        Returns:
            Assigned specialist ID or None
        """
        best_match = self.find_best_match(request, available_specialists)

        if best_match:
            return best_match.id

        return None

    def load_balance(
        self,
        specialists: list[Specialist],
        current_load: dict[str, int],
    ) -> list[Specialist]:
        """
        Reorder specialists considering load balancing.

        Args:
            specialists: List of specialists
            current_load: Current consultation load per specialist

        Returns:
            Reordered list (least loaded first)
        """
        # Sort by current load (ascending)
        specialists_with_load = [
            (s, current_load.get(s.id, 0))
            for s in specialists
        ]

        specialists_with_load.sort(key=lambda x: x[1])

        return [s for s, _ in specialists_with_load]

    def match_with_load_balancing(
        self,
        request: ConsultRequest,
        available_specialists: list[Specialist],
        current_load: dict[str, int],
        max_load: int = 10,
    ) -> Optional[Specialist]:
        """
        Match considering load balancing.

        Args:
            request: Consultation request
            available_specialists: List of specialists
            current_load: Current load per specialist
            max_load: Maximum load per specialist

        Returns:
            Best matched specialist or None
        """
        # Filter out overloaded specialists
        specialists = [
            s for s in available_specialists
            if current_load.get(s.id, 0) < max_load
        ]

        if not specialists:
            return None

        # Get top matches
        top_matches = self.find_top_matches(request, specialists, limit=3)

        if not top_matches:
            return None

        # Among top matches, pick least loaded
        least_loaded = min(
            top_matches,
            key=lambda x: current_load.get(x[0].id, 0)
        )

        return least_loaded[0]

    def explain_match(
        self,
        request: ConsultRequest,
        specialist: Specialist,
    ) -> dict[str, Any]:
        """
        Explain why a specialist was matched.

        Args:
            request: Consultation request
            specialist: Matched specialist

        Returns:
            Explanation dictionary
        """
        score = self._calculate_match_score(request, specialist)

        reasons = []

        if specialist.primary_specialty == request.specialty_needed:
            reasons.append(f"Specializes in {specialist.primary_specialty}")

        if specialist.verification_level == VerificationLevel.EXPERT:
            reasons.append("Expert-level verification")
        elif specialist.verification_level == VerificationLevel.CERTIFIED:
            reasons.append("Board certified")

        if specialist.average_rating >= 4.5:
            reasons.append(f"Highly rated ({specialist.average_rating:.1f}/5.0)")

        if specialist.total_consultations >= 50:
            reasons.append(f"Extensive experience ({specialist.total_consultations} consultations)")

        expected_hours = {
            ConsultPriority.ROUTINE: 24,
            ConsultPriority.URGENT: 6,
            ConsultPriority.EMERGENCY: 1,
        }
        expected = expected_hours[request.priority]
        if specialist.average_response_time_hours <= expected:
            reasons.append(f"Fast response (avg {specialist.average_response_time_hours:.1f}h)")

        if request.preferred_language in specialist.languages:
            reasons.append(f"Speaks {request.preferred_language}")

        return {
            "match_score": score,
            "reasons": reasons,
            "specialist": {
                "id": specialist.id,
                "name": specialist.name,
                "specialty": specialist.primary_specialty,
                "rating": specialist.average_rating,
                "consultations": specialist.total_consultations,
                "verification_level": specialist.verification_level.value,
            },
        }
