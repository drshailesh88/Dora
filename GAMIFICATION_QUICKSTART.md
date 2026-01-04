# Gamification Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### 1. Import the Module

```python
from src.gamification import GamificationService, get_gamification_service
```

### 2. Initialize with Storage

```python
# Your storage backend (implement this)
from src.core.storage import get_storage

storage = get_storage()
gamification = GamificationService(storage)

# Or use singleton
gamification = get_gamification_service(storage)
```

### 3. Track User Activity

```python
# Example: User completes a quiz
result = gamification.record_activity(
    user_id="dr_smith_123",
    activity_type="quiz",
    score=0.95,  # 95% score
)

# Auto-updates:
# - XP points (+25 or +50 for perfect)
# - Streak (daily activity)
# - Challenges (quiz completion)
# - Badges (check for new achievements)
# - Leaderboard (ranking update)

print(f"Earned {result['xp_earned']} XP!")
print(f"Streak: {result['streak']['current_streak']} days")
print(f"New badges: {len(result['new_badges'])}")
```

### 4. Get User Profile

```python
profile = gamification.get_user_profile("dr_smith_123")

# Returns everything:
print(f"Level {profile['level']['current_level']}")
print(f"XP: {profile['xp']['total']}")
print(f"Streak: {profile['streak']['current_streak']} days")
print(f"Badges: {profile['badges']['total']}")
print(f"Global Rank: #{profile['rank']['global']}")
```

### 5. Enable API Endpoints

```python
# In src/api/app.py

from src.api.gamification import router as gamification_router

app.include_router(gamification_router)
```

Now access at: `http://localhost:8000/api/game/`

### 6. Use Web UI

Navigate to: `http://localhost:3000/game`

Pages available:
- `/game` - Dashboard
- `/game/badges` - Badge collection
- `/game/leaderboard` - Rankings
- `/game/challenges` - Active challenges
- `/game/rewards` - Rewards shop

---

## 📖 Common Use Cases

### Award XP for Any Action

```python
gamification.award_custom_points(
    user_id="user123",
    xp_amount=100,
    reason="Completed first diagnosis"
)
```

### Check User's Badges

```python
badges = gamification.badges.get_user_badges("user123")
for badge in badges:
    print(f"{badge.badge_icon} {badge.badge_title}")
```

### Get Leaderboard

```python
from src.gamification import LeaderboardType, LeaderboardPeriod

leaderboard = gamification.leaderboard.get_leaderboard(
    leaderboard_type=LeaderboardType.GLOBAL,
    period=LeaderboardPeriod.WEEKLY,
)

for entry in leaderboard.rankings[:10]:
    print(f"#{entry['rank']} {entry['display_name']} - {entry['xp']} XP")
```

### Redeem Reward

```python
result = gamification.redeem_reward(
    user_id="user123",
    reward_id="reward_abc",
)

if result['success']:
    print(f"Code: {result['redemption_code']}")
    print(f"Instructions: {result['instructions']}")
```

---

## 🎯 Activity Types

Track these activities:

```python
# Learning Activities
record_activity(user_id, "query")        # +5 XP
record_activity(user_id, "query_deep")   # +10 XP
record_activity(user_id, "quiz")         # +25 XP
record_activity(user_id, "quiz_perfect") # +50 XP
record_activity(user_id, "article")      # +5 XP
record_activity(user_id, "video")        # +10 XP

# Community Activities
record_activity(user_id, "case")         # +100 XP
record_activity(user_id, "consultation") # +50 XP

# Engagement
record_activity(user_id, "login")        # +10 XP
record_activity(user_id, "rating")       # +5 XP
```

---

## 🛠️ Storage Implementation

You need to implement these methods:

```python
class GamificationStorage:
    """Interface for gamification storage"""

    # User Progress
    def get_user_progress(self, user_id: str) -> UserProgress: pass
    def save_user_progress(self, progress: UserProgress): pass

    # Points
    def save_points(self, points: Points): pass
    def get_points_history(self, user_id: str, limit: int, offset: int) -> list[Points]: pass

    # Streaks
    def get_streak(self, user_id: str) -> Streak: pass
    def save_streak(self, streak: Streak): pass

    # Badges
    def get_all_badges(self) -> list[Badge]: pass
    def get_user_badges(self, user_id: str) -> list[UserBadge]: pass
    def save_user_badge(self, user_badge: UserBadge): pass

    # Challenges
    def get_user_challenges(self, user_id: str, status: str) -> list[UserChallenge]: pass
    def save_user_challenge(self, challenge: UserChallenge): pass

    # Leaderboard
    def get_users_with_period_xp(self, period_start, period_end, ...) -> list[dict]: pass

    # Rewards
    def get_active_rewards(self, reward_type: Optional[str]) -> list[Reward]: pass
    def save_user_reward(self, user_reward: UserReward): pass
```

Use PostgreSQL, SQLite, or any database you prefer.

---

## ✅ Testing

```python
# Test the system
def test_gamification():
    storage = MockStorage()
    service = GamificationService(storage)

    # Record activity
    result = service.record_activity("test_user", "query")

    assert result['xp_earned'] == 5
    assert result['streak']['updated'] == True

    # Check profile
    profile = service.get_user_profile("test_user")

    assert profile['level']['current_level'] == 1
    assert profile['xp']['total'] >= 5

    print("✅ All tests passed!")

test_gamification()
```

---

## 🔥 Best Practices

### 1. Always Record Activity

Integrate activity tracking everywhere:

```python
# After query
gamification.record_activity(user_id, "query")

# After quiz
if score >= 1.0:
    gamification.record_activity(user_id, "quiz_perfect")
else:
    gamification.record_activity(user_id, "quiz")

# After login
gamification.record_activity(user_id, "login")
```

### 2. Check Badges Periodically

```python
# Check for new badges after significant actions
new_badges = gamification.badges.check_and_award_badges(user_id)

if new_badges:
    # Send notification
    for badge in new_badges:
        send_push_notification(
            user_id,
            f"🏆 You earned: {badge.badge_title}!"
        )
```

### 3. Update Leaderboards Async

```python
# Update rankings in background
import asyncio

async def update_rankings(user_id):
    await asyncio.to_thread(
        gamification.leaderboard.update_user_rankings,
        user_id
    )
```

### 4. Cache Expensive Queries

```python
from functools import lru_cache

@lru_cache(maxsize=1000, ttl=3600)  # 1 hour cache
def get_user_profile_cached(user_id):
    return gamification.get_user_profile(user_id)
```

---

## 🎨 UI Integration

### React Component Example

```tsx
import { useEffect, useState } from 'react';

function GamificationWidget({ userId }) {
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    fetch(`/api/game/profile?user_id=${userId}`)
      .then(res => res.json())
      .then(data => setProfile(data.profile));
  }, [userId]);

  if (!profile) return <div>Loading...</div>;

  return (
    <div className="gamification-widget">
      <div className="level">
        Level {profile.level.current_level}
      </div>
      <div className="xp-bar">
        <progress
          value={profile.xp.current_level}
          max={profile.xp.to_next_level}
        />
      </div>
      <div className="streak">
        🔥 {profile.streak.current_streak} day streak
      </div>
    </div>
  );
}
```

---

## 🐛 Troubleshooting

### Issue: Points not awarding

**Check:**
1. Storage implementation correct?
2. Activity type valid?
3. User exists in system?

```python
# Debug mode
points = gamification.points.award_points(
    user_id="test",
    event_type=PointEventType.QUERY,
    event_description="Test query",
    custom_xp=5,
)
print(f"Points awarded: {points}")
```

### Issue: Badges not unlocking

**Check:**
1. Criteria met?
2. Level requirement met?
3. Prerequisites earned?

```python
# Check badge progress
progress = gamification.badges.get_user_progress_for_badge(
    user_id="test",
    badge_key="streak_7_days",
)
print(f"Progress: {progress['current_value']} / {progress['target_value']}")
```

### Issue: Leaderboard not updating

**Check:**
1. Rankings update called?
2. Cache expired?
3. XP recorded?

```python
# Force update
gamification.leaderboard.update_user_rankings(user_id)

# Clear cache
# (Implementation-specific)
```

---

## 📞 Need Help?

1. **Read the docs:** `/GAMIFICATION_IMPLEMENTATION.md`
2. **Check the code:** `/src/gamification/`
3. **Test the API:** `/api/game/health`
4. **Review examples:** Above in this guide

---

**You're all set! Start gamifying Dora! 🚀**
