# Medical News Feed Module

Comprehensive medical news aggregation, personalization, and management system for Dora.

## Overview

The News module provides doctors with a personalized feed of medical news, research updates, guideline changes, drug approvals, and conference highlights. It's designed to help medical professionals stay current effortlessly.

## Features

### 🔄 Multi-Source Aggregation
- **PubMed** - Latest research articles and clinical studies
- **FDA/CDSCO** - Drug approvals and safety alerts
- **Medical Journals** - NEJM, Lancet, JAMA, BMJ via RSS
- **Guidelines** - AHA, ACC, ESC, ICMR, WHO updates
- **Conferences** - ACC, AHA, ASCO, ESC highlights

### 🤖 AI-Powered Summarization
- 3-5 bullet point summaries
- Key findings extraction
- Clinical implications ("What this means for your practice")
- Reading time estimation
- Automatic headline generation

### 🎯 Personalization
- Filtered by primary specialty
- Sub-specialty interests
- Category preferences (1-5 scale)
- Learning from reading behavior
- Relevance scoring algorithm
- Time-based reading lists

### 📋 Conference Coverage
- Major medical conference calendar
- Real-time updates during events
- Late-breaking trials
- Practice-changing presentations
- Keynote speaker tracking

### 📖 Guideline Tracking
- Monitor 10+ major guideline organizations
- Automatic change detection
- "What changed" summaries
- Implementation checklists
- Conflict detection with current practice

### 💊 Drug Approval Tracking
- FDA and CDSCO approvals
- New indications
- Generic and biosimilar approvals
- Safety updates and recalls
- Prescribing summaries

### 🔖 Bookmarks & Collections
- Save articles for later
- Organize into collections
- Tag and annotate
- Share with colleagues
- Export (JSON, CSV, HTML)
- Offline reading

## Architecture

```
src/news/
├── models.py          # Data models (Pydantic)
├── aggregator.py      # Multi-source news fetching
├── summarizer.py      # AI-powered summarization
├── personalization.py # Feed personalization & ranking
├── conferences.py     # Conference tracking
├── guidelines.py      # Guideline monitoring
├── approvals.py       # Drug approval tracking
├── bookmarks.py       # Bookmark management
├── service.py         # Main service layer
└── __init__.py        # Clean exports
```

## Data Models

### NewsArticle
Core model for all news content:
```python
NewsArticle(
    id="uuid",
    title="New ESC Guidelines for Heart Failure",
    source=NewsSource.ESC,
    category=NewsCategory.GUIDELINES,
    publication_date=datetime.utcnow(),
    summary="Brief summary...",
    key_findings=["Finding 1", "Finding 2"],
    clinical_implications="What this means...",
    specialty=["cardiology"],
    priority=NewsPriority.HIGH,
    reading_time_minutes=5,
)
```

### UserPreference
User personalization settings:
```python
UserPreference(
    user_id="user123",
    primary_specialty="cardiology",
    sub_specialties=["interventional_cardiology"],
    category_weights={
        "research": 5,
        "guidelines": 5,
        "drug_approvals": 4,
    },
    daily_digest=True,
    digest_time="07:00",
)
```

## API Endpoints

All endpoints are under `/api/v1/news`:

### Feed Endpoints
- `GET /feed` - Personalized news feed
- `GET /trending` - Trending articles
- `GET /breaking` - Breaking/urgent news
- `GET /article/{id}` - Article details
- `POST /search` - Search articles
- `GET /category/{category}` - Filter by category

### Specialized Content
- `GET /conferences` - Upcoming conferences
- `GET /guidelines` - Guideline updates
- `GET /approvals` - Drug approvals

### Bookmarks
- `POST /bookmark` - Bookmark article
- `GET /bookmarks` - User's bookmarks
- `POST /collections` - Create collection
- `GET /collections` - User's collections

### Preferences
- `GET /preferences` - Get user preferences
- `PUT /preferences` - Update preferences

### Engagement
- `POST /track/view` - Track article view
- `POST /track/read` - Track reading completion
- `GET /digest` - Daily digest
- `GET /reading-list` - Curated reading list

## Usage Examples

### Python Backend

```python
from src.news import NewsService, get_news_service

# Get service instance
service = await get_news_service()

# Get personalized feed
articles = await service.get_personalized_feed(
    user_id="user123",
    days_back=7,
    max_articles=50,
)

# Search articles
results = await service.search_articles(
    query="heart failure guidelines",
    user_id="user123",
    max_results=20,
)

# Bookmark article
bookmark = await service.bookmark_article(
    user_id="user123",
    article_id="article456",
    tags=["important", "guidelines"],
    notes="Review with team",
)

# Get daily digest
digest = await service.get_daily_digest(user_id="user123")
```

### REST API

```bash
# Get personalized feed
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.dora.com/api/v1/news/feed?days_back=7&max_articles=50"

# Get trending articles
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.dora.com/api/v1/news/trending?specialty=cardiology"

# Search articles
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "diabetes guidelines", "max_results": 20}' \
  "https://api.dora.com/api/v1/news/search"

# Bookmark article
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"article_id": "abc123", "tags": ["important"]}' \
  "https://api.dora.com/api/v1/news/bookmark"
```

## Web Integration

The news feed is integrated into the Next.js web app:

```
web/app/news/
├── page.tsx                    # Main news feed
├── article/[id]/page.tsx       # Article detail page
├── conferences/page.tsx        # Conference coverage
├── guidelines/page.tsx         # Guideline updates
└── bookmarks/page.tsx          # Saved articles
```

### Example Component

```tsx
"use client";

import { useEffect, useState } from "react";

export default function NewsFeed() {
  const [articles, setArticles] = useState([]);

  useEffect(() => {
    fetch("/api/v1/news/feed", {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => setArticles(data.articles));
  }, []);

  return (
    <div>
      {articles.map(article => (
        <ArticleCard key={article.id} article={article} />
      ))}
    </div>
  );
}
```

## Mobile Integration

Flutter mobile app screens:

```
mobile/lib/screens/news/
├── news_feed_screen.dart       # Main feed with tabs
├── article_detail_screen.dart  # Article view
├── bookmarks_screen.dart       # Saved articles
└── search_screen.dart          # Search interface
```

### Example Flutter

```dart
class NewsFeedScreen extends StatefulWidget {
  @override
  State<NewsFeedScreen> createState() => _NewsFeedScreenState();
}

class _NewsFeedScreenState extends State<NewsFeedScreen> {
  List<NewsArticle> articles = [];

  Future<void> fetchArticles() async {
    final response = await http.get(
      Uri.parse('/api/v1/news/feed'),
      headers: {'Authorization': 'Bearer $token'},
    );

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      setState(() {
        articles = (data['articles'] as List)
            .map((a) => NewsArticle.fromJson(a))
            .toList();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      itemCount: articles.length,
      itemBuilder: (context, index) {
        return ArticleCard(article: articles[index]);
      },
    );
  }
}
```

## Personalization Algorithm

The relevance scoring algorithm considers:

1. **Specialty Matching (40% weight)**
   - Primary specialty: 1.0
   - Sub-specialty: 0.8
   - Additional interests: 0.6

2. **Category Preference (20% weight)**
   - User-defined weights (1-5 scale)
   - Normalized to 0-1

3. **Source Credibility (15% weight)**
   - NEJM, Lancet, JAMA: 1.0
   - FDA, WHO, ICMR: 1.0
   - PubMed, BMJ: 0.95
   - Other: 0.7

4. **Keyword Matching (15% weight)**
   - Title and keyword overlap
   - User-defined interests

5. **Recency (10% weight)**
   - <1 day: 1.0
   - 1-3 days: 0.9
   - 3-7 days: 0.7
   - 7-14 days: 0.5
   - >14 days: 0.3

6. **Engagement Boost**
   - Past reading behavior
   - Bookmark patterns
   - Up to 20% boost

## Learning from Behavior

The system continuously learns from user behavior:

### Tracked Engagement
- Article views
- Reading completion
- Time spent reading
- Bookmarks
- Shares
- Likes/ratings

### Automatic Updates
- Category weights adjusted based on reading patterns
- Keywords extracted from bookmarked articles
- Specialty interests refined
- Optimal notification times learned

### Privacy
- All learning is local to user account
- No cross-user tracking
- Can be disabled in preferences
- Export and delete all data

## Background Jobs

### Hourly Jobs
- Fetch new articles from PubMed
- Check FDA approvals
- Scrape journal RSS feeds

### Daily Jobs
- Aggregate all sources
- Generate daily digests
- Update trending topics
- Clean up old articles

### Weekly Jobs
- Check guideline updates
- Fetch conference schedules
- Update user preferences from behavior

## Caching Strategy

### Article Cache
- Redis cache for feed responses
- TTL: 15 minutes for personalized feeds
- TTL: 5 minutes for trending
- TTL: 1 hour for articles

### Database Indexes
- `publication_date DESC` - Recent articles
- `category, publication_date` - Category filters
- `specialty, relevance_score` - Personalization
- `user_id, bookmarked_at` - Bookmarks

## Offline Support

### Mobile App
- Cache last 100 articles locally
- Download bookmarks for offline access
- Sync reading status when online
- Queue actions (bookmark, read) for sync

### Web App
- Service worker for offline viewing
- IndexedDB for article storage
- Background sync for engagement

## Notifications

### Push Notifications
- Breaking news (high priority only)
- Conference highlights
- Guideline updates
- Drug safety alerts

### Daily Digest
- Personalized email/push
- Configurable time (default 7:00 AM)
- Top 5-10 articles
- Trending topics
- Quick links

### Smart Scheduling
- Learn optimal notification times
- Respect quiet hours
- Batch non-urgent updates

## Testing

```bash
# Run tests
pytest tests/test_news/

# Test categories
tests/test_news/
├── test_aggregator.py      # Source aggregation
├── test_summarizer.py      # AI summarization
├── test_personalization.py # Ranking algorithm
├── test_bookmarks.py       # Bookmark management
├── test_api.py             # API endpoints
└── test_integration.py     # End-to-end tests
```

## Performance

### Benchmarks
- Feed generation: <500ms
- Article summarization: <2s
- Search: <200ms
- Bookmark: <100ms

### Scalability
- Handles 100K+ articles
- Supports 10K+ concurrent users
- Background jobs use queue (Celery/RQ)
- Horizontal scaling ready

## Future Enhancements

### Planned Features
- [ ] Audio summaries (text-to-speech)
- [ ] Video highlights from conferences
- [ ] AI-powered literature synthesis
- [ ] Collaborative reading lists
- [ ] Integration with EMR for patient-specific alerts
- [ ] Multi-language support
- [ ] Expert commentary on breaking news
- [ ] Journal club integration
- [ ] CME credit tracking

### Integrations
- [ ] Mendeley/Zotero citation export
- [ ] Slack/Teams notifications
- [ ] Apple Health for reading habits
- [ ] WhatsApp digest delivery

## License

Part of the Dora medical knowledge platform.
See LICENSE file for details.

## Contact

For questions or contributions:
- Project: https://github.com/drshailesh88/Dora
- Issues: https://github.com/drshailesh88/Dora/issues
