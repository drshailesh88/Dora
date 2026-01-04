"""
News Aggregation Module

Fetches medical news from multiple sources including PubMed, medical journals,
regulatory bodies, and conference proceedings.
"""

import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any, Optional
from urllib.parse import urlencode

import aiohttp
from bs4 import BeautifulSoup

from .models import (
    NewsArticle,
    NewsCategory,
    NewsPriority,
    NewsSource,
)

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for API calls."""

    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.min_interval = 60.0 / calls_per_minute
        self.last_call: dict[str, float] = {}

    async def wait(self, source: str) -> None:
        """Wait if necessary to respect rate limit."""
        now = asyncio.get_event_loop().time()
        last = self.last_call.get(source, 0)
        elapsed = now - last

        if elapsed < self.min_interval:
            await asyncio.sleep(self.min_interval - elapsed)

        self.last_call[source] = asyncio.get_event_loop().time()


class NewsAggregator:
    """Aggregate medical news from multiple sources."""

    def __init__(
        self,
        pubmed_api_key: Optional[str] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ):
        self.pubmed_api_key = pubmed_api_key
        self.session = session
        self.rate_limiter = RateLimiter(calls_per_minute=60)
        self.seen_articles: set[str] = set()  # For deduplication

    async def __aenter__(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _generate_article_hash(
        self,
        title: str,
        publication_date: datetime,
        source: str,
    ) -> str:
        """Generate unique hash for article deduplication."""
        content = f"{title.lower()}{publication_date.date()}{source}"
        return hashlib.md5(content.encode()).hexdigest()

    def _is_duplicate(self, article_hash: str) -> bool:
        """Check if article has already been seen."""
        if article_hash in self.seen_articles:
            return True
        self.seen_articles.add(article_hash)
        return False

    async def fetch_pubmed_articles(
        self,
        query: str,
        max_results: int = 20,
        days_back: int = 7,
        specialties: Optional[list[str]] = None,
    ) -> list[NewsArticle]:
        """
        Fetch recent articles from PubMed.

        Args:
            query: Search query
            max_results: Maximum number of results
            days_back: Number of days to look back
            specialties: Filter by specialties

        Returns:
            List of news articles
        """
        await self.rate_limiter.wait("pubmed")

        try:
            # Build PubMed query
            date_from = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y/%m/%d")

            # Add specialty filters if provided
            if specialties:
                specialty_filter = " OR ".join([f"{s}[MeSH Terms]" for s in specialties])
                query = f"({query}) AND ({specialty_filter})"

            # Search PubMed
            search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            search_params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
                "datetype": "pdat",
                "reldate": days_back,
                "sort": "pub_date",
            }

            if self.pubmed_api_key:
                search_params["api_key"] = self.pubmed_api_key

            async with self.session.get(search_url, params=search_params) as response:
                search_data = await response.json()
                pmids = search_data.get("esearchresult", {}).get("idlist", [])

            if not pmids:
                return []

            # Fetch article details
            fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",
            }

            if self.pubmed_api_key:
                fetch_params["api_key"] = self.pubmed_api_key

            await self.rate_limiter.wait("pubmed")

            async with self.session.get(fetch_url, params=fetch_params) as response:
                xml_data = await response.text()

            # Parse XML and create articles
            articles = self._parse_pubmed_xml(xml_data)
            logger.info(f"Fetched {len(articles)} articles from PubMed")
            return articles

        except Exception as e:
            logger.error(f"Error fetching PubMed articles: {e}")
            return []

    def _parse_pubmed_xml(self, xml_data: str) -> list[NewsArticle]:
        """Parse PubMed XML response."""
        articles = []
        soup = BeautifulSoup(xml_data, "xml")

        for article_tag in soup.find_all("PubmedArticle"):
            try:
                # Extract basic info
                article = article_tag.find("Article")
                if not article:
                    continue

                title = article.find("ArticleTitle")
                title_text = title.get_text() if title else "Untitled"

                # Extract abstract
                abstract_tag = article.find("Abstract")
                abstract = ""
                if abstract_tag:
                    abstract_texts = abstract_tag.find_all("AbstractText")
                    abstract = " ".join([a.get_text() for a in abstract_texts])

                # Extract authors
                authors = []
                author_list = article.find("AuthorList")
                if author_list:
                    for author in author_list.find_all("Author"):
                        last_name = author.find("LastName")
                        fore_name = author.find("ForeName")
                        if last_name and fore_name:
                            authors.append(f"{fore_name.get_text()} {last_name.get_text()}")

                # Extract journal
                journal_tag = article.find("Journal")
                journal_name = ""
                if journal_tag:
                    journal_title = journal_tag.find("Title")
                    if journal_title:
                        journal_name = journal_title.get_text()

                # Extract publication date
                pub_date = article_tag.find("PubDate")
                pub_datetime = self._parse_pubmed_date(pub_date)

                # Extract PMID
                pmid_tag = article_tag.find("PMID")
                pmid = pmid_tag.get_text() if pmid_tag else None

                # Extract keywords/MeSH terms
                keywords = []
                mesh_list = article_tag.find("MeshHeadingList")
                if mesh_list:
                    for mesh in mesh_list.find_all("DescriptorName", limit=5):
                        keywords.append(mesh.get_text())

                # Check for duplicates
                article_hash = self._generate_article_hash(
                    title_text, pub_datetime, "pubmed"
                )
                if self._is_duplicate(article_hash):
                    continue

                # Create article
                news_article = NewsArticle(
                    title=title_text,
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
                    source=NewsSource.PUBMED,
                    category=NewsCategory.RESEARCH,
                    authors=authors,
                    journal=journal_name,
                    publication_date=pub_datetime,
                    summary=abstract[:300] + "..." if len(abstract) > 300 else abstract,
                    full_text=abstract,
                    keywords=keywords,
                    pubmed_id=pmid,
                    reading_time_minutes=max(3, len(abstract.split()) // 200),
                )

                articles.append(news_article)

            except Exception as e:
                logger.error(f"Error parsing PubMed article: {e}")
                continue

        return articles

    def _parse_pubmed_date(self, pub_date_tag) -> datetime:
        """Parse PubMed publication date."""
        if not pub_date_tag:
            return datetime.utcnow()

        year = pub_date_tag.find("Year")
        month = pub_date_tag.find("Month")
        day = pub_date_tag.find("Day")

        year_val = int(year.get_text()) if year else datetime.utcnow().year

        # Handle month names
        month_val = 1
        if month:
            month_text = month.get_text()
            if month_text.isdigit():
                month_val = int(month_text)
            else:
                month_map = {
                    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
                    "May": 5, "Jun": 6, "Jul": 7, "Aug": 8,
                    "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
                }
                month_val = month_map.get(month_text[:3], 1)

        day_val = int(day.get_text()) if day else 1

        try:
            return datetime(year_val, month_val, day_val)
        except ValueError:
            return datetime.utcnow()

    async def fetch_fda_approvals(
        self,
        days_back: int = 30,
        max_results: int = 10,
    ) -> list[NewsArticle]:
        """
        Fetch recent FDA drug approvals.

        Args:
            days_back: Number of days to look back
            max_results: Maximum number of results

        Returns:
            List of drug approval articles
        """
        await self.rate_limiter.wait("fda")

        try:
            # FDA API endpoint
            # Note: This is a simplified example. Real implementation would use FDA's openFDA API
            url = "https://api.fda.gov/drug/drugsfda.json"

            # Calculate date range
            date_from = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y%m%d")

            params = {
                "search": f"openfda.approval_date:[{date_from} TO {datetime.utcnow().strftime('%Y%m%d')}]",
                "limit": max_results,
            }

            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    logger.warning(f"FDA API returned status {response.status}")
                    return []

                data = await response.json()
                results = data.get("results", [])

            articles = []
            for item in results:
                try:
                    # Extract approval info
                    products = item.get("products", [{}])[0]
                    openfda = item.get("openfda", {})

                    brand_name = openfda.get("brand_name", ["Unknown"])[0]
                    generic_name = openfda.get("generic_name", ["Unknown"])[0]
                    manufacturer = openfda.get("manufacturer_name", ["Unknown"])[0]

                    # Parse approval date
                    submission_date = products.get("approval_date", "")
                    try:
                        approval_date = datetime.strptime(submission_date, "%Y%m%d")
                    except:
                        approval_date = datetime.utcnow()

                    # Check for duplicates
                    article_hash = self._generate_article_hash(
                        brand_name, approval_date, "fda"
                    )
                    if self._is_duplicate(article_hash):
                        continue

                    article = NewsArticle(
                        title=f"FDA Approves {brand_name} ({generic_name})",
                        url=f"https://www.accessdata.fda.gov/scripts/cder/daf/",
                        source=NewsSource.FDA,
                        category=NewsCategory.DRUG_APPROVALS,
                        publication_date=approval_date,
                        summary=f"FDA has approved {brand_name} ({generic_name}) by {manufacturer}.",
                        key_findings=[
                            f"Brand name: {brand_name}",
                            f"Generic name: {generic_name}",
                            f"Manufacturer: {manufacturer}",
                        ],
                        priority=NewsPriority.HIGH,
                        reading_time_minutes=3,
                    )

                    articles.append(article)

                except Exception as e:
                    logger.error(f"Error parsing FDA approval: {e}")
                    continue

            logger.info(f"Fetched {len(articles)} FDA approvals")
            return articles

        except Exception as e:
            logger.error(f"Error fetching FDA approvals: {e}")
            return []

    async def fetch_guideline_updates(
        self,
        organizations: Optional[list[str]] = None,
        days_back: int = 90,
    ) -> list[NewsArticle]:
        """
        Fetch recent guideline updates from major organizations.

        Args:
            organizations: Filter by organizations (AHA, ACC, ESC, etc.)
            days_back: Number of days to look back

        Returns:
            List of guideline update articles
        """
        # Note: This is a placeholder implementation
        # Real implementation would scrape/fetch from various guideline sources
        articles = []

        # Example sources to monitor:
        guideline_sources = {
            "AHA": "https://www.heart.org/guidelines",
            "ACC": "https://www.acc.org/guidelines",
            "ESC": "https://www.escardio.org/guidelines",
            "ICMR": "https://www.icmr.gov.in/guidelines.html",
            "WHO": "https://www.who.int/publications/guidelines",
        }

        if organizations:
            guideline_sources = {
                k: v for k, v in guideline_sources.items()
                if k in organizations
            }

        # In production, this would actually fetch and parse guideline pages
        logger.info(f"Would fetch guidelines from {len(guideline_sources)} sources")

        return articles

    async def fetch_conference_updates(
        self,
        conferences: Optional[list[str]] = None,
        days_back: int = 30,
    ) -> list[NewsArticle]:
        """
        Fetch conference highlights and late-breaking trials.

        Args:
            conferences: Filter by conference names
            days_back: Number of days to look back

        Returns:
            List of conference highlight articles
        """
        # Note: This is a placeholder implementation
        # Real implementation would integrate with conference APIs or scrape sites
        articles = []

        major_conferences = [
            "ACC",  # American College of Cardiology
            "AHA",  # American Heart Association
            "ASCO",  # American Society of Clinical Oncology
            "ASH",  # American Society of Hematology
            "ESC",  # European Society of Cardiology
        ]

        logger.info(f"Would fetch conference updates from {len(major_conferences)} conferences")

        return articles

    async def fetch_from_medical_journals(
        self,
        journals: Optional[list[str]] = None,
        days_back: int = 7,
        max_results: int = 10,
    ) -> list[NewsArticle]:
        """
        Fetch recent articles from major medical journals.

        Args:
            journals: Filter by journal names
            days_back: Number of days to look back
            max_results: Maximum results per journal

        Returns:
            List of journal articles
        """
        # Note: This would integrate with journal RSS feeds or APIs
        # NEJM, Lancet, JAMA, BMJ all provide RSS feeds

        journal_rss = {
            "NEJM": "https://www.nejm.org/action/showFeed?type=etoc&feed=rss&jc=nejm",
            "Lancet": "https://www.thelancet.com/rssfeed/lancet_current.xml",
            "JAMA": "https://jamanetwork.com/rss/site_1/1.xml",
        }

        if journals:
            journal_rss = {k: v for k, v in journal_rss.items() if k in journals}

        articles = []

        # In production, would parse RSS feeds
        logger.info(f"Would fetch from {len(journal_rss)} journal RSS feeds")

        return articles

    async def aggregate_all(
        self,
        specialty: Optional[str] = None,
        days_back: int = 7,
        max_results_per_source: int = 10,
    ) -> list[NewsArticle]:
        """
        Aggregate news from all sources.

        Args:
            specialty: Filter by medical specialty
            days_back: Number of days to look back
            max_results_per_source: Max results per source

        Returns:
            Aggregated and deduplicated list of articles
        """
        logger.info(f"Aggregating news for specialty: {specialty or 'all'}")

        # Fetch from all sources in parallel
        tasks = [
            self.fetch_pubmed_articles(
                query=specialty or "medicine",
                max_results=max_results_per_source,
                days_back=days_back,
                specialties=[specialty] if specialty else None,
            ),
            self.fetch_fda_approvals(
                days_back=days_back,
                max_results=max_results_per_source,
            ),
            # self.fetch_guideline_updates(days_back=days_back),
            # self.fetch_conference_updates(days_back=days_back),
            # self.fetch_from_medical_journals(days_back=days_back),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine all articles
        all_articles = []
        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Error in aggregation: {result}")

        # Sort by publication date (newest first)
        all_articles.sort(key=lambda x: x.publication_date, reverse=True)

        logger.info(f"Aggregated {len(all_articles)} total articles")
        return all_articles

    def normalize_article(self, raw_article: dict[str, Any]) -> NewsArticle:
        """
        Normalize article from any source to NewsArticle format.

        Args:
            raw_article: Raw article data from any source

        Returns:
            Normalized NewsArticle
        """
        # This handles converting various formats to our standard NewsArticle model
        # Useful when integrating with different APIs that return different schemas

        return NewsArticle(
            title=raw_article.get("title", "Untitled"),
            url=raw_article.get("url", ""),
            source=NewsSource(raw_article.get("source", "other")),
            category=NewsCategory(raw_article.get("category", "research")),
            publication_date=raw_article.get("publication_date", datetime.utcnow()),
            summary=raw_article.get("summary", ""),
            authors=raw_article.get("authors", []),
            journal=raw_article.get("journal"),
            keywords=raw_article.get("keywords", []),
        )


async def get_news_aggregator() -> NewsAggregator:
    """Get news aggregator instance."""
    # In production, would get API keys from config
    return NewsAggregator()
