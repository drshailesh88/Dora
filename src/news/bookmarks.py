"""
News Bookmarks and Collections Module

Manages saved articles, reading lists, collections, and sharing.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

from .models import (
    NewsArticle,
    NewsBookmark,
    NewsCollection,
    ReadingStatus,
)

logger = logging.getLogger(__name__)


class BookmarkManager:
    """Manage news bookmarks and collections."""

    def __init__(self):
        # In production, would use database
        self.bookmarks: dict[str, NewsBookmark] = {}
        self.collections: dict[str, NewsCollection] = {}

    async def bookmark_article(
        self,
        user_id: str,
        article: NewsArticle,
        collection_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        notes: Optional[str] = None,
    ) -> NewsBookmark:
        """
        Bookmark an article.

        Args:
            user_id: User ID
            article: Article to bookmark
            collection_id: Optional collection ID
            tags: Optional tags
            notes: Optional user notes

        Returns:
            Created bookmark
        """
        # Check if already bookmarked
        existing = await self.get_bookmark(user_id, article.id)
        if existing:
            logger.info(f"Article {article.id} already bookmarked by user {user_id}")
            return existing

        bookmark = NewsBookmark(
            user_id=user_id,
            article_id=article.id,
            article_title=article.title,
            article_url=article.url,
            article_source=article.source,
            collection_id=collection_id,
            tags=tags or [],
            notes=notes,
        )

        # Store bookmark
        self.bookmarks[bookmark.id] = bookmark

        # Update collection if specified
        if collection_id:
            await self._update_collection_count(collection_id)

        logger.info(f"Bookmarked article {article.id} for user {user_id}")
        return bookmark

    async def unbookmark_article(
        self,
        user_id: str,
        article_id: str,
    ) -> bool:
        """
        Remove bookmark.

        Args:
            user_id: User ID
            article_id: Article ID

        Returns:
            Success status
        """
        bookmark = await self.get_bookmark(user_id, article_id)
        if not bookmark:
            return False

        # Update collection count if needed
        if bookmark.collection_id:
            await self._update_collection_count(bookmark.collection_id, delta=-1)

        # Remove bookmark
        del self.bookmarks[bookmark.id]

        logger.info(f"Removed bookmark for article {article_id}")
        return True

    async def get_bookmark(
        self,
        user_id: str,
        article_id: str,
    ) -> Optional[NewsBookmark]:
        """
        Get bookmark for article.

        Args:
            user_id: User ID
            article_id: Article ID

        Returns:
            Bookmark if exists
        """
        for bookmark in self.bookmarks.values():
            if bookmark.user_id == user_id and bookmark.article_id == article_id:
                return bookmark
        return None

    async def get_user_bookmarks(
        self,
        user_id: str,
        collection_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        reading_status: Optional[ReadingStatus] = None,
        limit: int = 50,
    ) -> list[NewsBookmark]:
        """
        Get user's bookmarks.

        Args:
            user_id: User ID
            collection_id: Filter by collection
            tags: Filter by tags
            reading_status: Filter by reading status
            limit: Maximum results

        Returns:
            List of bookmarks
        """
        bookmarks = [
            b for b in self.bookmarks.values()
            if b.user_id == user_id
        ]

        # Apply filters
        if collection_id:
            bookmarks = [b for b in bookmarks if b.collection_id == collection_id]

        if tags:
            bookmarks = [
                b for b in bookmarks
                if any(tag in b.tags for tag in tags)
            ]

        if reading_status:
            bookmarks = [
                b for b in bookmarks
                if b.reading_status == reading_status
            ]

        # Sort by bookmarked date (newest first)
        bookmarks.sort(key=lambda x: x.bookmarked_at, reverse=True)

        return bookmarks[:limit]

    async def update_bookmark(
        self,
        bookmark_id: str,
        tags: Optional[list[str]] = None,
        notes: Optional[str] = None,
        reading_status: Optional[ReadingStatus] = None,
        reading_progress: Optional[int] = None,
    ) -> Optional[NewsBookmark]:
        """
        Update bookmark metadata.

        Args:
            bookmark_id: Bookmark ID
            tags: Updated tags
            notes: Updated notes
            reading_status: Updated reading status
            reading_progress: Updated reading progress

        Returns:
            Updated bookmark
        """
        bookmark = self.bookmarks.get(bookmark_id)
        if not bookmark:
            return None

        if tags is not None:
            bookmark.tags = tags

        if notes is not None:
            bookmark.notes = notes

        if reading_status is not None:
            bookmark.reading_status = reading_status

        if reading_progress is not None:
            bookmark.reading_progress = reading_progress

        bookmark.last_accessed = datetime.utcnow()

        return bookmark

    async def create_collection(
        self,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        emoji: Optional[str] = None,
        color: Optional[str] = None,
        is_public: bool = False,
    ) -> NewsCollection:
        """
        Create a new collection.

        Args:
            user_id: User ID
            name: Collection name
            description: Optional description
            emoji: Optional emoji icon
            color: Optional color code
            is_public: Whether collection is public

        Returns:
            Created collection
        """
        collection = NewsCollection(
            user_id=user_id,
            name=name,
            description=description,
            emoji=emoji,
            color=color,
            is_public=is_public,
        )

        self.collections[collection.id] = collection

        logger.info(f"Created collection '{name}' for user {user_id}")
        return collection

    async def update_collection(
        self,
        collection_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        emoji: Optional[str] = None,
        color: Optional[str] = None,
        is_public: Optional[bool] = None,
    ) -> Optional[NewsCollection]:
        """
        Update collection metadata.

        Args:
            collection_id: Collection ID
            name: Updated name
            description: Updated description
            emoji: Updated emoji
            color: Updated color
            is_public: Updated public status

        Returns:
            Updated collection
        """
        collection = self.collections.get(collection_id)
        if not collection:
            return None

        if name is not None:
            collection.name = name

        if description is not None:
            collection.description = description

        if emoji is not None:
            collection.emoji = emoji

        if color is not None:
            collection.color = color

        if is_public is not None:
            collection.is_public = is_public

        collection.updated_at = datetime.utcnow()

        return collection

    async def delete_collection(
        self,
        collection_id: str,
        user_id: str,
    ) -> bool:
        """
        Delete a collection.

        Args:
            collection_id: Collection ID
            user_id: User ID (for verification)

        Returns:
            Success status
        """
        collection = self.collections.get(collection_id)
        if not collection or collection.user_id != user_id:
            return False

        # Remove collection from all bookmarks
        for bookmark in self.bookmarks.values():
            if bookmark.collection_id == collection_id:
                bookmark.collection_id = None

        # Delete collection
        del self.collections[collection_id]

        logger.info(f"Deleted collection {collection_id}")
        return True

    async def get_user_collections(
        self,
        user_id: str,
    ) -> list[NewsCollection]:
        """
        Get user's collections.

        Args:
            user_id: User ID

        Returns:
            List of collections
        """
        collections = [
            c for c in self.collections.values()
            if c.user_id == user_id
        ]

        # Sort by updated date
        collections.sort(key=lambda x: x.updated_at, reverse=True)

        return collections

    async def add_to_collection(
        self,
        bookmark_id: str,
        collection_id: str,
    ) -> bool:
        """
        Add bookmark to collection.

        Args:
            bookmark_id: Bookmark ID
            collection_id: Collection ID

        Returns:
            Success status
        """
        bookmark = self.bookmarks.get(bookmark_id)
        collection = self.collections.get(collection_id)

        if not bookmark or not collection:
            return False

        # Verify ownership
        if bookmark.user_id != collection.user_id:
            return False

        old_collection = bookmark.collection_id
        bookmark.collection_id = collection_id

        # Update counts
        if old_collection:
            await self._update_collection_count(old_collection, delta=-1)
        await self._update_collection_count(collection_id)

        return True

    async def remove_from_collection(
        self,
        bookmark_id: str,
    ) -> bool:
        """
        Remove bookmark from its collection.

        Args:
            bookmark_id: Bookmark ID

        Returns:
            Success status
        """
        bookmark = self.bookmarks.get(bookmark_id)
        if not bookmark or not bookmark.collection_id:
            return False

        collection_id = bookmark.collection_id
        bookmark.collection_id = None

        await self._update_collection_count(collection_id, delta=-1)

        return True

    async def share_bookmark(
        self,
        bookmark_id: str,
        share_with_user_ids: list[str],
    ) -> bool:
        """
        Share bookmark with other users.

        Args:
            bookmark_id: Bookmark ID
            share_with_user_ids: List of user IDs to share with

        Returns:
            Success status
        """
        bookmark = self.bookmarks.get(bookmark_id)
        if not bookmark:
            return False

        # Add to shared_with list
        for user_id in share_with_user_ids:
            if user_id not in bookmark.shared_with:
                bookmark.shared_with.append(user_id)

        logger.info(f"Shared bookmark {bookmark_id} with {len(share_with_user_ids)} users")
        return True

    async def get_reading_list(
        self,
        user_id: str,
        limit: int = 20,
    ) -> list[NewsBookmark]:
        """
        Get reading list (unread bookmarks).

        Args:
            user_id: User ID
            limit: Maximum results

        Returns:
            List of unread bookmarks
        """
        return await self.get_user_bookmarks(
            user_id=user_id,
            reading_status=ReadingStatus.UNREAD,
            limit=limit,
        )

    async def mark_as_read(
        self,
        bookmark_id: str,
    ) -> bool:
        """
        Mark bookmark as read.

        Args:
            bookmark_id: Bookmark ID

        Returns:
            Success status
        """
        return await self.update_bookmark(
            bookmark_id=bookmark_id,
            reading_status=ReadingStatus.READ,
            reading_progress=100,
        ) is not None

    async def archive_bookmark(
        self,
        bookmark_id: str,
    ) -> bool:
        """
        Archive a bookmark.

        Args:
            bookmark_id: Bookmark ID

        Returns:
            Success status
        """
        bookmark = self.bookmarks.get(bookmark_id)
        if not bookmark:
            return False

        bookmark.reading_status = ReadingStatus.ARCHIVED
        bookmark.archived_at = datetime.utcnow()

        return True

    async def get_archived_bookmarks(
        self,
        user_id: str,
        limit: int = 50,
    ) -> list[NewsBookmark]:
        """
        Get archived bookmarks.

        Args:
            user_id: User ID
            limit: Maximum results

        Returns:
            List of archived bookmarks
        """
        return await self.get_user_bookmarks(
            user_id=user_id,
            reading_status=ReadingStatus.ARCHIVED,
            limit=limit,
        )

    async def search_bookmarks(
        self,
        user_id: str,
        query: str,
        tags: Optional[list[str]] = None,
    ) -> list[NewsBookmark]:
        """
        Search user's bookmarks.

        Args:
            user_id: User ID
            query: Search query
            tags: Filter by tags

        Returns:
            Matching bookmarks
        """
        bookmarks = await self.get_user_bookmarks(user_id, tags=tags)

        # Filter by query
        query_lower = query.lower()
        matching = [
            b for b in bookmarks
            if (
                query_lower in b.article_title.lower()
                or (b.notes and query_lower in b.notes.lower())
            )
        ]

        return matching

    async def get_bookmark_statistics(
        self,
        user_id: str,
    ) -> dict:
        """
        Get bookmark statistics for user.

        Args:
            user_id: User ID

        Returns:
            Statistics
        """
        all_bookmarks = await self.get_user_bookmarks(user_id, limit=10000)

        stats = {
            "total_bookmarks": len(all_bookmarks),
            "unread": len([b for b in all_bookmarks if b.reading_status == ReadingStatus.UNREAD]),
            "read": len([b for b in all_bookmarks if b.reading_status == ReadingStatus.READ]),
            "archived": len([b for b in all_bookmarks if b.reading_status == ReadingStatus.ARCHIVED]),
            "total_collections": len(await self.get_user_collections(user_id)),
            "tags": self._get_tag_statistics(all_bookmarks),
        }

        return stats

    def _get_tag_statistics(
        self,
        bookmarks: list[NewsBookmark],
    ) -> dict[str, int]:
        """Get tag usage statistics."""
        tag_counts = {}

        for bookmark in bookmarks:
            for tag in bookmark.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return tag_counts

    async def _update_collection_count(
        self,
        collection_id: str,
        delta: int = 1,
    ) -> None:
        """Update collection article count."""
        collection = self.collections.get(collection_id)
        if collection:
            collection.article_count = max(0, collection.article_count + delta)
            collection.updated_at = datetime.utcnow()

    async def export_bookmarks(
        self,
        user_id: str,
        format: str = "json",
    ) -> str:
        """
        Export bookmarks.

        Args:
            user_id: User ID
            format: Export format (json, csv, html)

        Returns:
            Exported data as string
        """
        bookmarks = await self.get_user_bookmarks(user_id, limit=10000)

        if format == "json":
            import json
            return json.dumps([b.model_dump() for b in bookmarks], indent=2)

        elif format == "csv":
            # Create CSV
            csv_lines = ["Title,URL,Source,Tags,Bookmarked At"]
            for b in bookmarks:
                tags = ";".join(b.tags)
                csv_lines.append(
                    f'"{b.article_title}",{b.article_url},{b.article_source.value},"{tags}",{b.bookmarked_at}'
                )
            return "\n".join(csv_lines)

        elif format == "html":
            # Create HTML bookmarks file
            html = ["<!DOCTYPE NETSCAPE-Bookmark-file-1>", "<HTML>", "<HEAD>", "<TITLE>Bookmarks</TITLE>", "</HEAD>", "<BODY>", "<H1>Bookmarks</H1>", "<DL><p>"]

            for b in bookmarks:
                html.append(f'    <DT><A HREF="{b.article_url}">{b.article_title}</A>')

            html.extend(["</DL><p>", "</BODY>", "</HTML>"])
            return "\n".join(html)

        return ""


async def get_bookmark_manager() -> BookmarkManager:
    """Get bookmark manager instance."""
    return BookmarkManager()
