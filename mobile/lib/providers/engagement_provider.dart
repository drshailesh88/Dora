import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_service.dart';

/// Provider for morning briefing
final morningBriefingProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  return await api.get('/engagement/briefing');
});

/// Provider for clinical alerts
final clinicalAlertsProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  final result = await api.get('/engagement/alerts');
  return List<Map<String, dynamic>>.from(result['alerts'] ?? []);
});

/// Provider for trending queries
final trendingQueriesProvider = FutureProvider.family<List<Map<String, dynamic>>, String>(
  (ref, specialty) async {
    final api = ref.watch(apiServiceProvider);
    final result = await api.get('/engagement/trending?specialty=$specialty');
    return List<Map<String, dynamic>>.from(result['trending'] ?? []);
  },
);

/// Provider for clinical pearl of the day
final clinicalPearlProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  return await api.get('/engagement/pearl');
});
