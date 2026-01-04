# Mobile Gamification Integration

## Overview

This directory contains Flutter screens for the Dora gamification system.

## Screens to Implement

### 1. Game Dashboard (`game_dashboard_screen.dart`)

Main gamification hub showing:
- User level and XP progress with animated progress bar
- Current streak with fire animation
- Showcased badges in carousel
- Quick stats (total queries, quizzes, etc.)
- Active challenges preview
- Leaderboard position

**Widgets:**
- `XPProgressBar` - Animated level progress
- `StreakFireWidget` - Animated streak counter
- `BadgeCarousel` - Horizontal scrolling badges
- `QuickStatsCard` - Stats grid

### 2. Badges Screen (`badges_screen.dart`)

Badge collection interface:
- GridView of all badges
- Filter by category (tabs)
- Badge details on tap
- Progress indicators for locked badges
- Showcase badge toggle

**Widgets:**
- `BadgeCard` - Individual badge display
- `BadgeDetailModal` - Full badge information
- `BadgeProgressIndicator` - Circular progress for locked badges

### 3. Leaderboard Screen (`leaderboard_screen.dart`)

Rankings display:
- Period selector (Daily/Weekly/Monthly/All-Time)
- Type selector (Global/Specialty/Regional/Friends)
- Ranked list with avatars
- User's position highlighted
- Pull-to-refresh

**Widgets:**
- `LeaderboardEntry` - Single ranking item
- `RankMedal` - Medal for top 3
- `UserHighlight` - Highlighted current user position

### 4. Challenges Screen (`challenges_screen.dart`)

Active challenges:
- Expandable sections for Daily/Weekly/Monthly
- Progress bars for each challenge
- Completion animations
- XP reward display

**Widgets:**
- `ChallengeCard` - Individual challenge
- `ChallengeProgress` - Animated progress bar
- `CompletionCelebration` - Confetti animation on complete

### 5. Rewards Screen (`rewards_screen.dart`)

Rewards shop:
- GridView of available rewards
- Filter by type
- Affordability indicators
- Redemption modal
- My rewards tab

**Widgets:**
- `RewardCard` - Reward display with pricing
- `RedemptionModal` - Confirmation and code display
- `AffordabilityBadge` - Shows if user can afford

## Widgets Library

### Core Widgets (`/widgets/game/`)

1. **`xp_bar.dart`** - Animated XP progress bar
2. **`level_badge.dart`** - Level number with tier icon
3. **`streak_fire.dart`** - Animated fire emoji for streaks
4. **`badge_display.dart`** - Badge with tier and icon
5. **`challenge_card.dart`** - Challenge with progress
6. **`reward_card.dart`** - Reward with pricing
7. **`leaderboard_entry.dart`** - Ranking list item
8. **`celebration_overlay.dart`** - Full-screen celebrations

## API Integration

### API Service (`/services/gamification_api.dart`)

```dart
class GamificationApi {
  static const baseUrl = '/api/game';

  Future<GamificationProfile> getProfile(String userId);
  Future<List<Badge>> getBadges(String userId);
  Future<List<Badge>> getAvailableBadges(String userId);
  Future<Leaderboard> getLeaderboard({
    LeaderboardType type,
    Period period,
  });
  Future<Challenges> getChallenges(String userId);
  Future<List<Reward>> getRewards(String userId);
  Future<RedemptionResult> redeemReward(String userId, String rewardId);
  Future<ActivityResult> recordActivity(String userId, String activityType);
}
```

## State Management

Use **Provider** or **Riverpod** for state management:

```dart
// Providers
final gamificationProfileProvider = StateNotifierProvider<GamificationProfileNotifier, GamificationProfile>();
final badgesProvider = FutureProvider<List<Badge>>();
final leaderboardProvider = FutureProvider<Leaderboard>();
final challengesProvider = FutureProvider<Challenges>();
```

## Animations

### 1. Level Up Animation
- Scale up level badge
- Confetti particles
- Sound effect (optional)
- Haptic feedback

### 2. Badge Earned
- Badge reveal with glow
- Sparkle particles
- Badge shake animation

### 3. Streak Fire
- Pulsing animation
- Color gradient based on streak length
- Flame particles for high streaks (30+)

### 4. XP Gain
- Number count-up animation
- Progress bar fill animation
- Glow effect on level up

## Sample Implementation

### XP Progress Widget

```dart
class XPProgressBar extends StatelessWidget {
  final int currentXP;
  final int totalXP;
  final int level;

  @override
  Widget build(BuildContext context) {
    final progress = currentXP / totalXP;

    return Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text('Level $level'),
            Text('$currentXP / $totalXP XP'),
          ],
        ),
        SizedBox(height: 8),
        LinearProgressIndicator(
          value: progress,
          backgroundColor: Colors.grey[300],
          valueColor: AlwaysStoppedAnimation(Colors.blue),
          minHeight: 12,
        ),
      ],
    );
  }
}
```

## Theme Integration

Match Dora's theme colors:
- Primary: Medical blue (#0066CC)
- Accent: Success green (#10B981)
- Warning: Streak orange (#F59E0B)
- Badges: Tier-specific colors (Bronze, Silver, Gold, Platinum)

## Testing

Create widget tests for:
1. XP progress calculations
2. Badge filtering
3. Leaderboard sorting
4. Challenge progress updates
5. Reward affordability logic

## Next Steps

1. Implement `game_dashboard_screen.dart`
2. Create reusable widgets in `/widgets/game/`
3. Set up API service with proper error handling
4. Add animations and celebrations
5. Test on iOS and Android
6. Add offline caching for better UX

## Resources

- Flutter Animations: https://flutter.dev/docs/development/ui/animations
- Provider State Management: https://pub.dev/packages/provider
- Confetti Package: https://pub.dev/packages/confetti
- Lottie Animations: https://pub.dev/packages/lottie
