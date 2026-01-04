# Engagement Module

Daily engagement system for building doctor habits and ensuring Dora becomes part of their daily workflow.

## Overview

The engagement module provides:
- **Daily Briefings**: Morning digest with patient previews, clinical pearls, and key updates
- **Alert System**: Research papers, guideline updates, drug recalls
- **Trending Queries**: What other doctors in your specialty are asking
- **Clinical Pearls**: Daily evidence-based clinical tips
- **Smart Scheduling**: Learns optimal notification times
- **Analytics**: Track engagement, identify at-risk users

## Architecture

```
src/engagement/
├── models.py           # Data models
├── briefing.py         # Morning briefing generator
├── alerts.py           # Research, guideline, and drug alerts
├── trending.py         # Trending query analysis
├── pearls.py           # Clinical pearl management
├── scheduler.py        # Smart notification scheduling
├── analytics.py        # Engagement analytics
├── service.py          # Main engagement service
└── __init__.py         # Clean exports
```

## Quick Start

### Backend

```python
from src.engagement import get_engagement_service

service = get_engagement_service()

# Generate daily briefing
briefing = await service.generate_daily_briefing(
    user_id="user_123",
    user_profile={"specialty": "cardiology", "name": "Dr. Sharma"},
    emr_data={"patients_today": [...]},
)

# Get trending queries
trending = service.get_trending(
    specialty="cardiology",
    period=TrendingPeriod.LAST_7D,
)

# Get daily pearl
pearl = service.get_daily_pearl(
    user_id="user_123",
    specialty="cardiology",
)

# Track engagement
service.analytics.track_briefing_open(user_id, briefing_id, datetime.now())
score = service.get_engagement_score(user_id)
```

### API Endpoints

```bash
# Get daily briefing
GET /api/v1/engagement/briefing

# Get alerts
GET /api/v1/engagement/alerts?unread_only=true

# Get trending queries
GET /api/v1/engagement/trending?period=last_7d

# Get daily clinical pearl
GET /api/v1/engagement/pearls/daily

# Get engagement insights
GET /api/v1/engagement/stats

# Update notification preferences
PUT /api/v1/engagement/preferences
```

### Web Components

```tsx
import { MorningBriefing } from '@/components/engagement/morning-briefing';
import { AlertBell } from '@/components/engagement/alert-bell';
import { TrendingSidebar } from '@/components/engagement/trending-sidebar';
import { ClinicalPearlCard } from '@/components/engagement/clinical-pearl-card';

// In your dashboard
<MorningBriefing />
<TrendingSidebar />
<ClinicalPearlCard />

// In app header
<AlertBell />
```

### Mobile Components (Flutter)

```dart
import 'package:dora/widgets/engagement/briefing_card.dart';
import 'package:dora/widgets/engagement/alert_badge.dart';
import 'package:dora/widgets/engagement/trending_list.dart';
import 'package:dora/widgets/engagement/pearl_widget.dart';

// In your screens
BriefingCard(briefing: briefing, onItemTap: handleItemTap);
AlertBadge(unreadCount: count, onTap: openAlerts);
TrendingList(queries: queries, onQueryTap: handleQuery);
PearlWidget(pearl: pearl, onRefresh: fetchNewPearl);
```

## Features

### 1. Daily Briefing

Generated each morning (5-8am based on user preference):

```python
# Items included:
- Patient preview from EMR (today's appointments)
- Clinical pearl relevant to specialty
- Critical alerts (drug recalls, guideline changes)
- Trending queries in specialty
- New research papers (top 2)
```

**Personalization:**
- Specialty-specific content
- Learns optimal delivery time
- Respects quiet hours
- Configurable max items (3-15)

### 2. Alert System

**Types:**
- Research papers (PubMed new publications)
- Guideline updates (ICMR, WHO, specialty societies)
- Drug recalls/safety alerts (FDA, CDSCO)
- Drug interactions (based on prescriptions)

**Severity Levels:**
- Critical: Immediate delivery, override quiet hours
- High: Deliver within 1 hour
- Medium: Batch with next scheduled delivery
- Low: Include in daily briefing only

**Relevance Filtering:**
```python
# Only send alerts relevant to:
- User's specialty
- User's common conditions
- User's recent queries
- User's active patients (drug alerts)
```

### 3. Trending Queries

Shows what other doctors are asking:

**Aggregation:**
- By specialty
- By geography (city, state, country)
- By time period (24h, 7d, 30d)
- Anonymized queries

**Trend Detection:**
- Rising: Moving up in rankings
- Falling: Moving down
- New: First appearance
- Stable: Consistent position

**Example:**
```
🔥 Trending in Cardiology (Mumbai, Last 7d)
1. ↗️ What is first-line treatment for HFrEF? (250 queries)
2. 🆕 SGLT2i in non-diabetic heart failure (180 queries)
3. → Beta blocker dosing in AFib (150 queries)
```

### 4. Clinical Pearls

Evidence-based clinical tips:

**Content:**
- Title: Short, memorable
- Content: 1-2 sentence pearl
- Explanation: Detailed rationale
- Citations: Source references
- Evidence level: High/Medium/Low

**Formats:**
- Regular: Just the pearl
- Quiz: Multiple choice question

**Examples:**
```
💡 Beta Blockers First in AFib
Remember: BB before CCB in rate control for AFib with heart failure

💡 Metformin Start Low Go Slow
Metformin: Start 500mg, go slow → 2000mg over 4 weeks

💡 Fever in Infants
Fever in <3 months = always septic workup (blood, urine, LP)
```

### 5. Smart Scheduling

**Learning:**
- Tracks when user opens notifications
- Identifies active hours (when user is online)
- Adjusts delivery times for maximum open rate

**Quiet Hours:**
- Default: 21:00 - 07:00
- Configurable per user
- Critical alerts can override

**Batching:**
- Groups low-priority notifications
- Sends at end of day or next morning
- Reduces notification fatigue

### 6. Engagement Analytics

**Metrics Tracked:**
- Briefing open rate
- Item click-through rate
- Alert acknowledgment rate
- Query activity
- Pearl views
- Session duration

**Engagement Score (0-100):**
```python
score = (
    briefing_opened * 15 +
    briefing_items_clicked * 3 (max 15) +
    alert_open_rate * 20 +
    queries_made * 5 (max 30) +
    pearls_viewed * 5 (max 10) +
    trending_viewed * 2 (max 10)
)
```

**Churn Prevention:**
- Identifies at-risk users (score < 20 for 3+ days)
- Identifies dormant users (no activity 7+ days)
- Triggers re-engagement campaigns

## Background Jobs

Set up these cron jobs:

```bash
# Generate daily briefings (5am daily)
0 5 * * * python -m src.engagement.service run_daily_briefing_job

# Fetch new alerts (hourly)
0 * * * * python -m src.engagement.service run_alert_fetch_job

# Compute trending queries (every 6 hours)
0 */6 * * * python -m src.engagement.service run_trending_computation_job

# Process notification queue (continuous)
python -m src.engagement.scheduler process_queue &
```

## Configuration

### User Preferences

```python
preferences = NotificationPreference(
    user_id="user_123",

    # Briefing
    briefing_enabled=True,
    briefing_time="07:30",
    briefing_days=[0, 1, 2, 3, 4, 5],  # Mon-Sat

    # Alerts
    research_alerts=True,
    guideline_alerts=True,
    drug_alerts=True,
    critical_only=False,

    # Delivery
    push_notifications=True,
    email_digest=True,

    # Timing
    quiet_hours_enabled=True,
    quiet_start="22:00",
    quiet_end="07:00",

    # Content
    max_briefing_items=7,
    include_trending=True,
    include_pearls=True,

    # Learning
    learn_from_behavior=True,
)
```

## Testing

```python
import pytest
from src.engagement import get_engagement_service

def test_briefing_generation():
    service = get_engagement_service()

    briefing = await service.generate_daily_briefing(
        user_id="test_user",
        user_profile={"specialty": "cardiology"},
    )

    assert briefing.greeting
    assert briefing.summary_line
    assert len(briefing.items) > 0

def test_trending_computation():
    analyzer = TrendingAnalyzer()

    # Track some queries
    for i in range(10):
        analyzer.track_query(
            query_text="What is first-line for hypertension?",
            user_id=f"user_{i}",
            specialty="cardiology",
        )

    trending = analyzer.compute_trending(specialty="cardiology")
    assert len(trending) > 0
    assert trending[0].rank == 1

def test_engagement_scoring():
    analytics = EngagementAnalytics()

    analytics.track_briefing_open("user_1", "briefing_1", datetime.now())
    analytics.track_query("user_1")

    score = analytics.get_engagement_score("user_1")
    assert score > 0
```

## Database Schema

```sql
-- Daily briefings
CREATE TABLE engagement_briefings (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    date DATE NOT NULL,
    greeting TEXT,
    summary_line TEXT,
    items JSONB,
    specialty VARCHAR,
    patient_count_today INT,
    generated_at TIMESTAMP,
    delivered_at TIMESTAMP,
    opened_at TIMESTAMP,
    UNIQUE(user_id, date)
);

-- Alerts
CREATE TABLE engagement_alerts (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    alert_type VARCHAR NOT NULL,
    severity VARCHAR,
    title TEXT,
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMP,
    delivered_at TIMESTAMP,
    opened_at TIMESTAMP,
    acknowledged_at TIMESTAMP,
    dismissed BOOLEAN DEFAULT FALSE
);

-- Engagement metrics
CREATE TABLE engagement_metrics (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    date DATE NOT NULL,
    briefing_opened BOOLEAN,
    briefing_items_clicked INT,
    alerts_received INT,
    alerts_opened INT,
    queries_made INT,
    pearls_viewed INT,
    engagement_score FLOAT,
    UNIQUE(user_id, date)
);

-- Clinical pearls history
CREATE TABLE engagement_pearl_history (
    user_id VARCHAR,
    pearl_id VARCHAR,
    viewed_at TIMESTAMP,
    PRIMARY KEY (user_id, pearl_id)
);

-- Notification preferences
CREATE TABLE engagement_preferences (
    user_id VARCHAR PRIMARY KEY,
    briefing_enabled BOOLEAN,
    briefing_time TIME,
    research_alerts BOOLEAN,
    quiet_hours_enabled BOOLEAN,
    quiet_start TIME,
    quiet_end TIME,
    preferences JSONB,
    updated_at TIMESTAMP
);
```

## Monitoring

**Key Metrics:**
- Daily briefing open rate (target: >60%)
- Alert acknowledgment rate (target: >80%)
- Average engagement score (target: >50)
- Churn rate (at-risk users / total users)
- Notification delivery success rate

**Alerts:**
- Engagement score drop >20 points
- Churn rate increase >5%
- Notification delivery failure rate >10%

## Future Enhancements

1. **Personalized Content Ranking**: Use ML to rank briefing items
2. **Predictive Alerts**: Anticipate what users will need
3. **Cohort Recommendations**: "Doctors like you also viewed..."
4. **Voice Briefings**: "Alexa, what's my Dora briefing?"
5. **Weekly Digest**: Email summary of week's highlights
6. **Gamification**: Streaks, badges, leaderboards
7. **Social Features**: Share pearls with colleagues

## License

Internal DocAssist project - Confidential
