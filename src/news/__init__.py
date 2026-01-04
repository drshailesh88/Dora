"""
News Module - Medical News Feed

Comprehensive medical news aggregation, personalization, and management.

Features:
- Multi-source news aggregation (PubMed, FDA, journals, conferences)
- AI-powered summarization and key findings extraction
- Personalized feed based on specialty and interests
- Conference coverage and late-breaking trials
- Guideline update tracking
- Drug approval notifications
- Bookmarks and collections
- Reading lists and offline access
"""

from .aggregator import NewsAggregator, get_news_aggregator
from .approvals import DrugApprovalTracker, get_drug_approval_tracker
from .bookmarks import BookmarkManager, get_bookmark_manager
from .conferences import ConferenceTracker, get_conference_tracker
from .guidelines import GuidelineTracker, get_guideline_tracker
from .models import (
    ConferenceHighlight,
    DrugApproval,
    GuidelineUpdate,
    NewsArticle,
    NewsBookmark,
    NewsCategory,
    NewsCollection,
    NewsEngagement,
    NewsPriority,
    NewsSource,
    ReadingStatus,
    ResearchBreakthrough,
    UserPreference,
)
from .personalization import NewsPersonalizer, get_news_personalizer
from .service import NewsService, get_news_service
from .summarizer import NewsSummarizer, get_news_summarizer

__all__ = [
    # Models
    "NewsArticle",
    "ConferenceHighlight",
    "GuidelineUpdate",
    "DrugApproval",
    "ResearchBreakthrough",
    "NewsCategory",
    "NewsPriority",
    "NewsSource",
    "ReadingStatus",
    "UserPreference",
    "NewsBookmark",
    "NewsCollection",
    "NewsEngagement",
    # Core services
    "NewsService",
    "get_news_service",
    # Aggregation
    "NewsAggregator",
    "get_news_aggregator",
    # Summarization
    "NewsSummarizer",
    "get_news_summarizer",
    # Personalization
    "NewsPersonalizer",
    "get_news_personalizer",
    # Bookmarks
    "BookmarkManager",
    "get_bookmark_manager",
    # Conferences
    "ConferenceTracker",
    "get_conference_tracker",
    # Guidelines
    "GuidelineTracker",
    "get_guideline_tracker",
    # Approvals
    "DrugApprovalTracker",
    "get_drug_approval_tracker",
]
