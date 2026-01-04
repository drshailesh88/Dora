"""
Case Library System

Manage anonymized case discussions for learning and CME.
"""

from datetime import datetime
from typing import Optional

from src.peers.models import (
    CaseDiscussion,
    CaseComment,
    CaseVisibility,
)


class CaseLibraryManager:
    """Manages case discussions and learning library."""

    def __init__(self):
        """Initialize case library manager."""
        # In production, use database
        self.cases: dict[str, CaseDiscussion] = {}
        self.comments: dict[str, list[CaseComment]] = {}

    def submit_case(
        self,
        submitted_by: str,
        title: str,
        specialty: str,
        case_category: str,
        case_presentation: str,
        diagnosis: str,
        learning_points: list[str],
        visibility: CaseVisibility = CaseVisibility.SPECIALTY,
        **kwargs,
    ) -> CaseDiscussion:
        """
        Submit a new case discussion.

        Args:
            submitted_by: Doctor ID
            title: Case title
            specialty: Specialty
            case_category: Category
            case_presentation: Full case presentation
            diagnosis: Diagnosis
            learning_points: Key learning points
            visibility: Who can see this case
            **kwargs: Additional fields

        Returns:
            CaseDiscussion object
        """
        case = CaseDiscussion(
            submitted_by=submitted_by,
            title=title,
            specialty=specialty,
            case_category=case_category,
            case_presentation=case_presentation,
            diagnosis=diagnosis,
            learning_points=learning_points,
            visibility=visibility,
            **kwargs,
        )

        self.cases[case.id] = case
        return case

    def get_case(self, case_id: str) -> Optional[CaseDiscussion]:
        """
        Get case by ID.

        Args:
            case_id: Case ID

        Returns:
            CaseDiscussion or None
        """
        case = self.cases.get(case_id)
        if case:
            # Increment view count
            case.view_count += 1
        return case

    def browse_cases(
        self,
        specialty: Optional[str] = None,
        category: Optional[str] = None,
        visibility: Optional[CaseVisibility] = None,
        featured_only: bool = False,
        user_specialty: Optional[str] = None,
        limit: int = 20,
    ) -> list[CaseDiscussion]:
        """
        Browse case discussions with filters.

        Args:
            specialty: Filter by specialty
            category: Filter by category
            visibility: Filter by visibility
            featured_only: Only featured cases
            user_specialty: User's specialty (for filtering)
            limit: Maximum results

        Returns:
            List of cases
        """
        results = []

        for case in self.cases.values():
            # Apply filters
            if specialty and case.specialty != specialty:
                continue

            if category and case.case_category != category:
                continue

            if featured_only and not case.is_featured:
                continue

            # Check visibility
            if visibility:
                if case.visibility != visibility:
                    continue
            else:
                # Apply default visibility rules
                if case.visibility == CaseVisibility.PRIVATE:
                    continue  # Private cases not shown in browse
                elif case.visibility == CaseVisibility.SPECIALTY:
                    if user_specialty and case.specialty != user_specialty:
                        continue

            results.append(case)

        # Sort by upvotes and view count
        results.sort(
            key=lambda c: (c.upvotes, c.view_count),
            reverse=True,
        )

        return results[:limit]

    def search_cases(
        self,
        query: str,
        specialty: Optional[str] = None,
        limit: int = 20,
    ) -> list[CaseDiscussion]:
        """
        Search cases by text.

        Args:
            query: Search query
            specialty: Filter by specialty
            limit: Maximum results

        Returns:
            List of matching cases
        """
        query_lower = query.lower()
        results = []

        for case in self.cases.values():
            # Skip private cases
            if case.visibility == CaseVisibility.PRIVATE:
                continue

            # Apply specialty filter
            if specialty and case.specialty != specialty:
                continue

            # Search in title, diagnosis, and case presentation
            searchable = (
                case.title.lower() + " " +
                case.diagnosis.lower() + " " +
                case.case_presentation.lower()
            )

            if query_lower in searchable:
                results.append(case)

        # Sort by relevance (simple: count of query word occurrences)
        results.sort(
            key=lambda c: c.title.lower().count(query_lower) +
                         c.diagnosis.lower().count(query_lower),
            reverse=True,
        )

        return results[:limit]

    def upvote_case(self, case_id: str, user_id: str) -> bool:
        """
        Upvote a case.

        Args:
            case_id: Case ID
            user_id: User who upvoted

        Returns:
            Success status
        """
        case = self.cases.get(case_id)
        if not case:
            return False

        # In production, track who upvoted to prevent duplicates
        case.upvotes += 1
        case.updated_at = datetime.utcnow()
        return True

    def feature_case(self, case_id: str) -> bool:
        """
        Feature a case.

        Args:
            case_id: Case ID

        Returns:
            Success status
        """
        case = self.cases.get(case_id)
        if not case:
            return False

        case.is_featured = True
        case.updated_at = datetime.utcnow()
        return True

    def add_comment(
        self,
        case_id: str,
        commenter_id: str,
        commenter_name: str,
        commenter_specialty: str,
        comment_text: str,
        parent_comment_id: Optional[str] = None,
        is_expert_opinion: bool = False,
    ) -> Optional[CaseComment]:
        """
        Add comment to case discussion.

        Args:
            case_id: Case ID
            commenter_id: Commenter user ID
            commenter_name: Commenter name
            commenter_specialty: Commenter specialty
            comment_text: Comment text
            parent_comment_id: Parent comment for threading
            is_expert_opinion: Mark as expert opinion

        Returns:
            CaseComment or None
        """
        case = self.cases.get(case_id)
        if not case:
            return None

        comment = CaseComment(
            case_id=case_id,
            commenter_id=commenter_id,
            commenter_name=commenter_name,
            commenter_specialty=commenter_specialty,
            comment_text=comment_text,
            parent_comment_id=parent_comment_id,
            is_expert_opinion=is_expert_opinion,
        )

        # Store comment
        if case_id not in self.comments:
            self.comments[case_id] = []
        self.comments[case_id].append(comment)

        # Update case comment count
        case.comment_count += 1
        case.updated_at = datetime.utcnow()

        return comment

    def get_comments(
        self,
        case_id: str,
        parent_only: bool = False,
    ) -> list[CaseComment]:
        """
        Get comments for a case.

        Args:
            case_id: Case ID
            parent_only: Only top-level comments

        Returns:
            List of comments
        """
        comments = self.comments.get(case_id, [])

        if parent_only:
            comments = [c for c in comments if c.parent_comment_id is None]

        # Sort by upvotes and creation date
        comments.sort(
            key=lambda c: (c.upvotes, c.created_at),
            reverse=True,
        )

        return comments

    def upvote_comment(self, comment_id: str, user_id: str) -> bool:
        """
        Upvote a comment.

        Args:
            comment_id: Comment ID
            user_id: User who upvoted

        Returns:
            Success status
        """
        # Find comment
        for case_comments in self.comments.values():
            for comment in case_comments:
                if comment.id == comment_id:
                    comment.upvotes += 1
                    comment.updated_at = datetime.utcnow()
                    return True

        return False

    def get_featured_cases(self, limit: int = 10) -> list[CaseDiscussion]:
        """
        Get featured cases.

        Args:
            limit: Maximum results

        Returns:
            List of featured cases
        """
        featured = [c for c in self.cases.values() if c.is_featured]
        featured.sort(
            key=lambda c: (c.upvotes, c.view_count),
            reverse=True,
        )
        return featured[:limit]

    def get_cases_by_specialty(
        self,
        specialty: str,
        limit: int = 20,
    ) -> list[CaseDiscussion]:
        """
        Get cases for a specialty.

        Args:
            specialty: Specialty name
            limit: Maximum results

        Returns:
            List of cases
        """
        return self.browse_cases(
            specialty=specialty,
            visibility=CaseVisibility.PUBLIC,
            limit=limit,
        )

    def get_my_cases(
        self,
        user_id: str,
    ) -> list[CaseDiscussion]:
        """
        Get cases submitted by user.

        Args:
            user_id: User ID

        Returns:
            List of cases
        """
        cases = [
            c for c in self.cases.values()
            if c.submitted_by == user_id
        ]

        cases.sort(key=lambda c: c.created_at, reverse=True)
        return cases

    def update_case(
        self,
        case_id: str,
        user_id: str,
        **updates,
    ) -> Optional[CaseDiscussion]:
        """
        Update case discussion.

        Args:
            case_id: Case ID
            user_id: User ID (must be submitter)
            **updates: Fields to update

        Returns:
            Updated case or None
        """
        case = self.cases.get(case_id)
        if not case or case.submitted_by != user_id:
            return None

        for key, value in updates.items():
            if hasattr(case, key):
                setattr(case, key, value)

        case.updated_at = datetime.utcnow()
        return case

    def delete_case(
        self,
        case_id: str,
        user_id: str,
    ) -> bool:
        """
        Delete case discussion.

        Args:
            case_id: Case ID
            user_id: User ID (must be submitter)

        Returns:
            Success status
        """
        case = self.cases.get(case_id)
        if not case or case.submitted_by != user_id:
            return False

        del self.cases[case_id]
        # Also delete comments
        if case_id in self.comments:
            del self.comments[case_id]

        return True

    def get_trending_cases(
        self,
        days: int = 7,
        limit: int = 10,
    ) -> list[CaseDiscussion]:
        """
        Get trending cases.

        Args:
            days: Number of days to consider
            limit: Maximum results

        Returns:
            List of trending cases
        """
        cutoff = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        cutoff = cutoff.replace(day=cutoff.day - days)

        recent_cases = [
            c for c in self.cases.values()
            if c.created_at >= cutoff
            and c.visibility != CaseVisibility.PRIVATE
        ]

        # Sort by engagement (upvotes + views + comments)
        recent_cases.sort(
            key=lambda c: c.upvotes * 10 + c.view_count + c.comment_count * 5,
            reverse=True,
        )

        return recent_cases[:limit]
