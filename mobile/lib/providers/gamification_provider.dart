import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_service.dart';

/// Provider for gamification stats
final gamificationStatsProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  return await api.get('/gamification/stats');
});

/// Provider for badges
final badgesProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  return await api.get('/gamification/badges');
});

/// Provider for leaderboard
final leaderboardProvider = FutureProvider.family<Map<String, dynamic>, (String, String)>(
  (ref, params) async {
    final (period, scope) = params;
    final api = ref.watch(apiServiceProvider);
    return await api.get('/gamification/leaderboard?period=$period&scope=$scope');
  },
);

/// Provider for challenges
final challengesProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  return await api.get('/gamification/challenges');
});

/// Provider to update challenge progress
final updateChallengeProvider = FutureProvider.family<void, (String, int)>(
  (ref, params) async {
    final (challengeId, progress) = params;
    final api = ref.watch(apiServiceProvider);
    await api.post('/gamification/challenges/$challengeId/progress', {'progress': progress});
    ref.invalidate(challengesProvider);
    ref.invalidate(gamificationStatsProvider);
  },
);
