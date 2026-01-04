"""
News API Endpoints

REST API for medical news feed, bookmarks, collections, and preferences.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.api.auth import get_current_user
from src.news import (
    NewsCategory,
    NewsService,
    ReadingStatus,
    UserPreference,
    get_news_service,
)

router = APIRouter(prefix="/api/v1/news", tags=["news"])


# Request/Response models
class FeedRequest(BaseModel):
    """Request for personalized feed."""

    days_back: int = Field(7, ge=1, le=30, description="Days to look back")
    max_articles: int = Field(50, ge=10, le=100, description="Max articles")
    category: Optional[str] = Field(None, description="Filter by category")


class FeedResponse(BaseModel):
    """Response with news feed."""

    success: bool
    articles: list[dict] = Field(default_factory=list)
    count: int = 0


class TrendingRequest(BaseModel):
    """Request for trending articles."""

    specialty: Optional[str] = None
    days_back: int = Field(3, ge=1, le=7)
    max_articles: int = Field(20, ge=5, le=50)


class SearchRequest(BaseModel):
    """Request for article search."""

    query: str = Field(..., min_length=2, description="Search query")
    category: Optional[str] = None
    max_results: int = Field(20, ge=5, le=50)


class BookmarkRequest(BaseModel):
    """Request to bookmark article."""

    article_id: str = Field(..., description="Article ID")
    collection_id: Optional[str] = Field(None, description="Collection ID")
    tags: list[str] = Field(default_factory=list, description="Tags")
    notes: Optional[str] = Field(None, description="User notes")


class BookmarkResponse(BaseModel):
    """Response with bookmark."""

    success: bool
    bookmark: Optional[dict] = None
    error: Optional[str] = None


class CollectionRequest(BaseModel):
    """Request to create collection."""

    name: str = Field(..., min_length=1, description="Collection name")
    description: Optional[str] = Field(None, description="Description")
    emoji: Optional[str] = Field(None, description="Emoji icon")
    color: Optional[str] = Field(None, description="Color code")


class CollectionResponse(BaseModel):
    """Response with collection."""

    success: bool
    collection: Optional[dict] = None
    error: Optional[str] = None


class PreferencesRequest(BaseModel):
    """Request to update preferences."""

    primary_specialty: str
    sub_specialties: list[str] = Field(default_factory=list)
    additional_interests: list[str] = Field(default_factory=list)
    category_weights: dict[str, int] = Field(default_factory=dict)
    daily_digest: bool = True
    digest_time: str = "07:00"


class TrackViewRequest(BaseModel):
    """Request to track article view."""

    article_id: str


class TrackReadRequest(BaseModel):
    """Request to track article read."""

    article_id: str
    reading_time_seconds: int = Field(..., ge=0)


# Endpoints
@router.get("/feed", response_model=FeedResponse)
async def get_personalized_feed(
    days_back: int = Query(7, ge=1, le=30),
    max_articles: int = Query(50, ge=10, le=100),
    category: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    service: NewsService = Depends(get_news_service),
):
    """
    Get personalized news feed for current user.

    Args:
        days_back: Number of days to look back
        max_articles: Maximum articles to return
        category: Optional category filter
        current_user: Current authenticated user
        service: News service

    Returns:
        Personalized news feed
    """
    try:
        user_id = current_user["id"]

        # Parse category
        cat_filter = None
        if category:
            try:
                cat_filter = NewsCategory(category)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid category: {category}",
                )

        articles = await service.get_personalized_feed(
            user_id=user_id,
            days_back=days_back,
            max_articles=max_articles,
            category=cat_filter,
        )

        return FeedResponse(
            success=True,
            articles=[a.model_dump() for a in articles],
            count=len(articles),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feed: {str(e)}",
        )


@router.get("/trending", response_model=FeedResponse)
async def get_trending_articles(
    specialty: Optional[str] = Query(None),
    days_back: int = Query(3, ge=1, le=7),
    max_articles: int = Query(20, ge=5, le=50),
    service: NewsService = Depends(get_news_service),
):
    """
    Get trending medical news articles.

    Args:
        specialty: Filter by specialty
        days_back: Number of days to look back
        max_articles: Maximum articles
        service: News service

    Returns:
        Trending articles
    """
    try:
        articles = await service.get_trending_articles(
            specialty=specialty,
            days_back=days_back,
            max_articles=max_articles,
        )

        return FeedResponse(
            success=True,
            articles=[a.model_dump() for a in articles],
            count=len(articles),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trending: {str(e)}",
        )


@router.get("/breaking", response_model=FeedResponse)
async def get_breaking_news(
    specialty: Optional[str] = Query(None),
    hours_back: int = Query(24, ge=1, le=72),
    service: NewsService = Depends(get_news_service),
):
    """
    Get breaking/urgent medical news.

    Args:
        specialty: Filter by specialty
        hours_back: Number of hours to look back
        service: News service

    Returns:
        Breaking news articles
    """
    try:
        articles = await service.get_breaking_news(
            specialty=specialty,
            hours_back=hours_back,
        )

        return FeedResponse(
            success=True,
            articles=[a.model_dump() for a in articles],
            count=len(articles),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get breaking news: {str(e)}",
        )


@router.get("/article/{article_id}")
async def get_article(
    article_id: str,
    current_user: dict = Depends(get_current_user),
    service: NewsService = Depends(get_news_service),
):
    """
    Get article details by ID.

    Args:
        article_id: Article ID
        current_user: Current user
        service: News service

    Returns:
        Article details
    """
    try:
        # Track view
        await service.track_article_view(
            user_id=current_user["id"],
            article_id=article_id,
        )

        article = await service.get_article(article_id)

        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Article {article_id} not found",
            )

        # Get similar articles
        similar = await service.get_similar_articles(
            article_id=article_id,
            max_results=5,
        )

        return {
            "success": True,
            "article": article.model_dump(),
            "similar": [a.model_dump() for a in similar],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get article: {str(e)}",
        )


@router.post("/search", response_model=FeedResponse)
async def search_articles(
    request: SearchRequest,
    current_user: dict = Depends(get_current_user),
    service: NewsService = Depends(get_news_service),
):
    """
    Search medical news articles.

    Args:
        request: Search request
        current_user: Current user
        service: News service

    Returns:
        Search results
    """
    try:
        user_id = current_user["id"]

        # Parse category
        cat_filter = None
        if request.category:
            try:
                cat_filter = NewsCategory(request.category)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid category: {request.category}",
                )

        articles = await service.search_articles(
            query=request.query,
            user_id=user_id,
            category=cat_filter,
            max_results=request.max_results,
        )

        return FeedResponse(
            success=True,
            articles=[a.model_dump() for a in articles],
            count=len(articles),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.get("/category/{category}", response_model=FeedResponse)
async def get_by_category(
    category: str,
    days_back: int = Query(7, ge=1, le=30),
    max_articles: int = Query(50, ge=10, le=100),
    current_user: dict = Depends(get_current_user),
    service: NewsService = Depends(get_news_service),
):
    """
    Get articles by category.

    Args:
        category: News category
        days_back: Days to look back
        max_articles: Maximum articles
        current_user: Current user
        service: News service

    Returns:
        Articles in category
    """
    try:
        # Validate category
        try:
            cat = NewsCategory(category)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category: {category}",
            )

        user_id = current_user["id"]

        articles = await service.get_personalized_feed(
            user_id=user_id,
            days_back=days_back,
            max_articles=max_articles,
            category=cat,
        )

        return FeedResponse(
            success=True,
            articles=[a.model_dump() for a in articles],
            count=len(articles),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get category: {str(e)}",
        )


@router.get("/conferences")
async def get_conference_updates(
    service: NewsService = Depends(get_news_service),
):
    """
    Get upcoming and recent conference updates.

    Args:
        service: News service

    Returns:
        Conference information
    """
    try:
        upcoming = service.conference_tracker.get_upcoming_conferences(
            months_ahead=6
        )

        return {
            "success": True,
            "upcoming_conferences": upcoming,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conferences: {str(e)}",
        )


@router.get("/guidelines")
async def get_guideline_updates(
    specialty: Optional[str] = Query(None),
    days_back: int = Query(90, ge=30, le=365),
    service: NewsService = Depends(get_news_service),
):
    """
    Get guideline updates.

    Args:
        specialty: Filter by specialty
        days_back: Days to look back
        service: News service

    Returns:
        Guideline updates
    """
    try:
        updates = await service.guideline_tracker.fetch_guideline_updates(
            specialty=specialty,
            days_back=days_back,
        )

        return {
            "success": True,
            "updates": [u.model_dump() for u in updates],
            "count": len(updates),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get guidelines: {str(e)}",
        )


@router.get("/approvals")
async def get_drug_approvals(
    regulatory_body: str = Query("FDA"),
    days_back: int = Query(30, ge=7, le=90),
    service: NewsService = Depends(get_news_service),
):
    """
    Get drug approvals.

    Args:
        regulatory_body: Regulatory body (FDA, CDSCO, etc.)
        days_back: Days to look back
        service: News service

    Returns:
        Drug approvals
    """
    try:
        approvals = await service.approval_tracker.fetch_recent_approvals(
            regulatory_body=regulatory_body,
            days_back=days_back,
        )

        return {
            "success": True,
            "approvals": [a.model_dump() for a in approvals],
            "count": len(approvals),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get approvals: {str(e)}",
        )


@router.post("/bookmark", response_model=BookmarkResponse)
async def bookmark_article(
    request: BookmarkRequest,
    current_user: dict = Depends(get_current_user),
    service: NewsService = Depends(get_news_service),
):
    """
    Bookmark an article.

    Args:
        request: Bookmark request
        current_user: Current user
        service: News service

    Returns:
        Created bookmark
    """
    try:
        user_id = current_user["id"]

        bookmark = await service.bookmark_article(
            user_id=user_id,
            article_id=request.article_id,
            collection_id=request.collection_id,
            tags=request.tags,
            notes=request.notes,
        )

        return BookmarkResponse(
            success=True,
            bookmark=bookmark.model_dump(),
        )

    except ValueError as e:
        return BookmarkResponse(
            success=False,
            error=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bookmark: {str(e)}",
        )


@router.get("/bookmarks")
async def get_bookmarks(
    collection_id: Optional[str] = Query(None),
    tags: Optional[list[str]] = Query(None),
    current_user: dict = Depends(get_current_user),
    service: NewsService = Depends(get_news_service),
):
    """
    Get user's bookmarks.

    Args:
        collection_id: Filter by collection
        tags: Filter by tags
        current_user: Current user
        service: News service

    Returns:
        User's bookmarks
    """
    try:
        user_id = current_user["id"]

        bookmarks = await service.get_user_bookmarks(
            user_id=user_id,
            collection_id=collection_id,
            tags=tags,
        )

        return {
            "success": True,
            "bookmarks": [b.model_dump() for b in bookmarks],
            "count": len(bookmarks),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get bookmarks: {str(e)}",
        )


@router.post("/collections", response_model=CollectionResponse)
async def create_collection(
    request: CollectionRequest,
    current_user: dict = Depends(get_current_user),
    service: NewsService = Depends(get_news_service),
):
    """
    Create bookmark collection.

    Args:
        request: Collection request
        current_user: Current user
        service: News service

    Returns:
        Created collection
    """
    try:
        user_id = current_user["id"]

        collection = await service.create_collection(
            user_id=user_id,
            name=request.name,
            description=request.description,
            emoji=request.emoji,
        )

        return CollectionResponse(
            success=True,
            collection=collection.model_dump(),
        )

    except Exception as e:
        return CollectionResponse(
            success=False,
            error=str(e),
        )


@router.get("/collections")
async def get_collections(
    current_user: dict = Depends(get_current_user),
    service: NewsService = Depends(get_news_service),
):
    """
    Get user's collections.

    Args:
        current_user: Current user
        service: News service

    Returns:
        User's collections
    """
    try:
        user_id = current_user["id"]

        collections = await service.get_user_collections(user_id)

        return {
            "success": True,
            "collections": [c.model_dump() for c in collections],
            "count": len(collections),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get collections: {str(e)}",
        )


@router.get("/preferences")
async def get_preferences(
    current_user: dict = Depends(get_current_user),
    service: NewsService = Depends(get_news_service),
):
    """
    Get user preferences.

    Args:
        current_user: Current user
        service: News service

    Returns:
        User preferences
    """
    try:
        user_id = current_user["id"]
        preferences = await service.get_user_preferences(user_id)

        return {
            "success": True,
            "preferences": preferences.model_dump(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get preferences: {str(e)}",
        )


@router.put("/preferences")
async def update_preferences(
    request: PreferencesRequest,
    current_user: dict = Depends(get_current_user),
    service: NewsService = Depends(get_news_service),
):
    """
    Update user preferences.

    Args:
        request: Preferences request
        current_user: Current user
        service: News service

    Returns:
        Updated preferences
    """
    try:
        user_id = current_user["id"]

        # Create preferences object
        preferences = UserPreference(
            user_id=user_id,
            primary_specialty=request.primary_specialty,
            sub_specialties=request.sub_specialties,
            additional_interests=request.additional_interests,
            category_weights=request.category_weights,
            daily_digest=request.daily_digest,
            digest_time=request.digest_time,
        )

        updated = await service.update_user_preferences(
            user_id=user_id,
            preferences=preferences,
        )

        return {
            "success": True,
            "preferences": updated.model_dump(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update preferences: {str(e)}",
        )


@router.get("/digest")
async def get_daily_digest(
    current_user: dict = Depends(get_current_user),
    service: NewsService = Depends(get_news_service),
):
    """
    Get daily news digest.

    Args:
        current_user: Current user
        service: News service

    Returns:
        Daily digest
    """
    try:
        user_id = current_user["id"]
        digest = await service.get_daily_digest(user_id)

        return digest

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get digest: {str(e)}",
        )


@router.get("/reading-list")
async def get_reading_list(
    time_available: int = Query(15, ge=5, le=60, description="Minutes available"),
    current_user: dict = Depends(get_current_user),
    service: NewsService = Depends(get_news_service),
):
    """
    Get curated reading list for available time.

    Args:
        time_available: Available reading time in minutes
        current_user: Current user
        service: News service

    Returns:
        Reading list
    """
    try:
        user_id = current_user["id"]

        articles = await service.get_reading_list(
            user_id=user_id,
            time_available_minutes=time_available,
        )

        total_time = sum(a.reading_time_minutes for a in articles)

        return {
            "success": True,
            "articles": [a.model_dump() for a in articles],
            "count": len(articles),
            "total_reading_time": total_time,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get reading list: {str(e)}",
        )


@router.post("/track/view")
async def track_view(
    request: TrackViewRequest,
    current_user: dict = Depends(get_current_user),
    service: NewsService = Depends(get_news_service),
):
    """
    Track article view.

    Args:
        request: Track request
        current_user: Current user
        service: News service

    Returns:
        Success status
    """
    try:
        await service.track_article_view(
            user_id=current_user["id"],
            article_id=request.article_id,
        )

        return {"success": True}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track view: {str(e)}",
        )


@router.post("/track/read")
async def track_read(
    request: TrackReadRequest,
    current_user: dict = Depends(get_current_user),
    service: NewsService = Depends(get_news_service),
):
    """
    Track article read completion.

    Args:
        request: Track request
        current_user: Current user
        service: News service

    Returns:
        Success status
    """
    try:
        await service.track_article_read(
            user_id=current_user["id"],
            article_id=request.article_id,
            reading_time_seconds=request.reading_time_seconds,
        )

        return {"success": True}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track read: {str(e)}",
        )


@router.get("/categories")
async def get_categories():
    """
    Get available news categories.

    Returns:
        List of categories
    """
    categories = [
        {
            "id": cat.value,
            "name": cat.value.replace("_", " ").title(),
        }
        for cat in NewsCategory
    ]

    return {
        "categories": categories,
    }
