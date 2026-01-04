import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_service.dart';

/// Provider for practice analytics
final practiceAnalyticsProvider = FutureProvider.family<Map<String, dynamic>, String>(
  (ref, period) async {
    final api = ref.watch(apiServiceProvider);
    return await api.get('/analytics/practice?period=$period');
  },
);

/// Provider for query analytics
final queryAnalyticsProvider = FutureProvider.family<Map<String, dynamic>, String>(
  (ref, period) async {
    final api = ref.watch(apiServiceProvider);
    return await api.get('/analytics/queries?period=$period');
  },
);

/// Provider for prescription analytics
final prescriptionAnalyticsProvider = FutureProvider.family<Map<String, dynamic>, String>(
  (ref, period) async {
    final api = ref.watch(apiServiceProvider);
    return await api.get('/analytics/prescriptions?period=$period');
  },
);

/// Provider for learning analytics
final learningAnalyticsProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  return await api.get('/analytics/learning');
});

/// Provider for insights
final insightsProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  final result = await api.get('/analytics/insights');
  return List<Map<String, dynamic>>.from(result['insights'] ?? []);
});

/// Provider for benchmarks
final benchmarksProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  return await api.get('/analytics/benchmarks');
});
