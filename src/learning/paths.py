"""
Learning Paths

Structured curricula for specialty-based learning.
"""

from datetime import datetime
from typing import Optional
import logging

from .models import (
    LearningPath,
    LearningModule,
    PathEnrollment,
    PathStatus,
    DifficultyLevel,
)

logger = logging.getLogger(__name__)


class PathManager:
    """Manages learning paths"""

    def __init__(self):
        self.paths: dict[str, LearningPath] = {}
        self.enrollments: dict[str, list[PathEnrollment]] = {}

    def create_path(
        self,
        title: str,
        description: str,
        specialty: str,
        modules: list[LearningModule],
        topics: Optional[list[str]] = None,
        difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE,
        total_cme_credits: Optional[float] = None,
        prerequisites: Optional[list[str]] = None,
        created_by: Optional[str] = None,
    ) -> LearningPath:
        """
        Create a learning path

        Args:
            title: Path title
            description: Path description
            specialty: Medical specialty
            modules: List of modules
            topics: Topics covered
            difficulty: Difficulty level
            total_cme_credits: Total CME credits (calculated if None)
            prerequisites: Required path IDs
            created_by: Creator user ID

        Returns:
            LearningPath
        """
        # Calculate total credits if not provided
        if total_cme_credits is None:
            total_cme_credits = sum(m.cme_credits for m in modules)

        # Calculate estimated hours
        estimated_hours = sum(m.estimated_minutes for m in modules) // 60

        path = LearningPath(
            title=title,
            description=description,
            specialty=specialty,
            topics=topics or [],
            modules=modules,
            total_modules=len(modules),
            difficulty=difficulty,
            estimated_hours=estimated_hours,
            total_cme_credits=total_cme_credits,
            prerequisites=prerequisites or [],
            created_by=created_by,
        )

        # Set path_id for all modules
        for module in modules:
            module.path_id = path.id

        self.paths[path.id] = path

        logger.info(f"Created learning path: {title} with {len(modules)} modules")

        return path

    def enroll_user(self, user_id: str, path_id: str) -> PathEnrollment:
        """
        Enroll user in a learning path

        Args:
            user_id: User ID
            path_id: Path ID

        Returns:
            PathEnrollment
        """
        path = self.paths.get(path_id)
        if not path:
            raise ValueError(f"Path not found: {path_id}")

        # Check prerequisites
        if path.prerequisites:
            completed_paths = self.get_completed_paths(user_id)
            completed_ids = set(e.path_id for e in completed_paths)

            for prereq_id in path.prerequisites:
                if prereq_id not in completed_ids:
                    prereq = self.paths.get(prereq_id)
                    prereq_title = prereq.title if prereq else prereq_id
                    raise ValueError(
                        f"Prerequisite not completed: {prereq_title}"
                    )

        # Check if already enrolled
        enrollments = self.get_user_enrollments(user_id)
        for enrollment in enrollments:
            if enrollment.path_id == path_id and enrollment.status != PathStatus.ABANDONED:
                logger.warning(f"User {user_id} already enrolled in path {path_id}")
                return enrollment

        # Create enrollment
        enrollment = PathEnrollment(
            user_id=user_id,
            path_id=path_id,
            status=PathStatus.NOT_STARTED,
            current_module_id=path.modules[0].id if path.modules else None,
        )

        if user_id not in self.enrollments:
            self.enrollments[user_id] = []

        self.enrollments[user_id].append(enrollment)

        # Update path analytics
        path.enrollment_count += 1

        logger.info(f"User {user_id} enrolled in path: {path.title}")

        return enrollment

    def start_path(self, user_id: str, path_id: str) -> PathEnrollment:
        """
        Start a learning path

        Args:
            user_id: User ID
            path_id: Path ID

        Returns:
            PathEnrollment
        """
        enrollment = self._get_enrollment(user_id, path_id)
        if not enrollment:
            raise ValueError(f"User not enrolled in path {path_id}")

        enrollment.status = PathStatus.IN_PROGRESS
        enrollment.started_at = datetime.utcnow()
        enrollment.last_activity_at = datetime.utcnow()

        logger.info(f"User {user_id} started path: {path_id}")

        return enrollment

    def complete_module(
        self,
        user_id: str,
        path_id: str,
        module_id: str,
        time_spent_seconds: int = 0,
        cme_credits_earned: float = 0.0,
    ) -> PathEnrollment:
        """
        Mark a module as completed

        Args:
            user_id: User ID
            path_id: Path ID
            module_id: Module ID
            time_spent_seconds: Time spent on module
            cme_credits_earned: CME credits earned

        Returns:
            Updated PathEnrollment
        """
        enrollment = self._get_enrollment(user_id, path_id)
        if not enrollment:
            raise ValueError(f"User not enrolled in path {path_id}")

        path = self.paths.get(path_id)
        if not path:
            raise ValueError(f"Path not found: {path_id}")

        # Mark module as completed
        if module_id not in enrollment.completed_module_ids:
            enrollment.completed_module_ids.append(module_id)

        # Update credits and time
        enrollment.cme_credits_earned += cme_credits_earned
        enrollment.total_time_spent_seconds += time_spent_seconds
        enrollment.last_activity_at = datetime.utcnow()

        # Calculate progress
        enrollment.progress_percentage = (
            len(enrollment.completed_module_ids) / path.total_modules * 100
        ) if path.total_modules > 0 else 0

        # Find next module
        current_module_index = None
        for i, module in enumerate(path.modules):
            if module.id == module_id:
                current_module_index = i
                break

        if current_module_index is not None and current_module_index < len(path.modules) - 1:
            # Move to next module
            next_module = path.modules[current_module_index + 1]
            enrollment.current_module_id = next_module.id
        else:
            # Path completed
            enrollment.current_module_id = None
            enrollment.status = PathStatus.COMPLETED
            enrollment.completed_at = datetime.utcnow()

            # Update path analytics
            path.completion_count += 1

            logger.info(f"User {user_id} completed path: {path.title}")

        logger.info(
            f"User {user_id} completed module {module_id} in path {path_id}. "
            f"Progress: {enrollment.progress_percentage:.1f}%"
        )

        return enrollment

    def abandon_path(self, user_id: str, path_id: str) -> PathEnrollment:
        """
        Mark a path as abandoned

        Args:
            user_id: User ID
            path_id: Path ID

        Returns:
            PathEnrollment
        """
        enrollment = self._get_enrollment(user_id, path_id)
        if not enrollment:
            raise ValueError(f"User not enrolled in path {path_id}")

        enrollment.status = PathStatus.ABANDONED
        logger.info(f"User {user_id} abandoned path: {path_id}")

        return enrollment

    def rate_path(
        self,
        user_id: str,
        path_id: str,
        rating: int,
        feedback: Optional[str] = None,
    ) -> PathEnrollment:
        """
        Rate a completed path

        Args:
            user_id: User ID
            path_id: Path ID
            rating: Rating (1-5)
            feedback: Optional feedback

        Returns:
            PathEnrollment
        """
        enrollment = self._get_enrollment(user_id, path_id)
        if not enrollment:
            raise ValueError(f"User not enrolled in path {path_id}")

        if enrollment.status != PathStatus.COMPLETED:
            raise ValueError("Can only rate completed paths")

        enrollment.rating = rating
        enrollment.feedback = feedback

        # Update path average rating
        path = self.paths.get(path_id)
        if path:
            # Recalculate average (simplified - would use proper weighted average in production)
            enrollments = self.get_path_enrollments(path_id)
            rated = [e for e in enrollments if e.rating is not None]
            if rated:
                path.average_rating = sum(e.rating for e in rated) / len(rated)

        logger.info(f"User {user_id} rated path {path_id}: {rating}/5")

        return enrollment

    def get_path(self, path_id: str) -> Optional[LearningPath]:
        """Get path by ID"""
        return self.paths.get(path_id)

    def get_all_paths(
        self,
        specialty: Optional[str] = None,
        difficulty: Optional[DifficultyLevel] = None,
        is_featured: Optional[bool] = None,
    ) -> list[LearningPath]:
        """
        Get all learning paths with optional filters

        Args:
            specialty: Filter by specialty
            difficulty: Filter by difficulty
            is_featured: Filter by featured status

        Returns:
            List of paths
        """
        paths = list(self.paths.values())

        if specialty:
            paths = [p for p in paths if p.specialty == specialty]

        if difficulty:
            paths = [p for p in paths if p.difficulty == difficulty]

        if is_featured is not None:
            paths = [p for p in paths if p.is_featured == is_featured]

        # Filter active paths only
        paths = [p for p in paths if p.is_active]

        return sorted(paths, key=lambda x: x.enrollment_count, reverse=True)

    def get_user_enrollments(self, user_id: str) -> list[PathEnrollment]:
        """Get user's path enrollments"""
        return self.enrollments.get(user_id, [])

    def get_active_enrollments(self, user_id: str) -> list[PathEnrollment]:
        """Get user's active enrollments"""
        enrollments = self.get_user_enrollments(user_id)
        return [
            e for e in enrollments
            if e.status in [PathStatus.NOT_STARTED, PathStatus.IN_PROGRESS]
        ]

    def get_completed_paths(self, user_id: str) -> list[PathEnrollment]:
        """Get user's completed paths"""
        enrollments = self.get_user_enrollments(user_id)
        return [e for e in enrollments if e.status == PathStatus.COMPLETED]

    def get_path_enrollments(self, path_id: str) -> list[PathEnrollment]:
        """Get all enrollments for a path"""
        all_enrollments = []
        for enrollments in self.enrollments.values():
            all_enrollments.extend([e for e in enrollments if e.path_id == path_id])
        return all_enrollments

    def get_recommended_paths(
        self,
        user_id: str,
        user_specialty: Optional[str] = None,
        limit: int = 5,
    ) -> list[LearningPath]:
        """
        Get recommended paths for user

        Args:
            user_id: User ID
            user_specialty: User's specialty
            limit: Max recommendations

        Returns:
            List of recommended paths
        """
        # Get completed paths
        completed = set(e.path_id for e in self.get_completed_paths(user_id))

        # Get enrolled paths
        enrolled = set(e.path_id for e in self.get_active_enrollments(user_id))

        # Filter paths
        candidates = [
            p for p in self.paths.values()
            if p.id not in completed and p.id not in enrolled and p.is_active
        ]

        # Prioritize by specialty match
        if user_specialty:
            specialty_matches = [p for p in candidates if p.specialty == user_specialty]
            other_paths = [p for p in candidates if p.specialty != user_specialty]
            candidates = specialty_matches + other_paths

        # Sort by popularity and rating
        candidates.sort(
            key=lambda x: (x.average_rating, x.enrollment_count),
            reverse=True
        )

        return candidates[:limit]

    def _get_enrollment(self, user_id: str, path_id: str) -> Optional[PathEnrollment]:
        """Get user's enrollment in a path"""
        enrollments = self.get_user_enrollments(user_id)
        for enrollment in enrollments:
            if enrollment.path_id == path_id:
                return enrollment
        return None


# Global path manager instance
_path_manager = PathManager()


def get_path_manager() -> PathManager:
    """Get the global path manager instance"""
    return _path_manager
