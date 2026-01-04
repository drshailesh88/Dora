import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_service.dart';

/// Provider for list of calculators
final calculatorsProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  final result = await api.get('/calculators');
  return List<Map<String, dynamic>>.from(result['calculators'] ?? []);
});

/// Provider to calculate result
final calculateProvider = FutureProvider.family<Map<String, dynamic>, (String, Map<String, dynamic>)>(
  (ref, params) async {
    final (calculatorId, inputs) = params;
    final api = ref.watch(apiServiceProvider);
    return await api.post('/calculators/$calculatorId/calculate', inputs);
  },
);

/// Provider for recent calculations
final recentCalculationsProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  final result = await api.get('/calculators/history');
  return List<Map<String, dynamic>>.from(result['history'] ?? []);
});

/// Provider for calculator favorites
final favoriteCalculatorsProvider = StateNotifierProvider<FavoriteCalculatorsNotifier, List<String>>(
  (ref) => FavoriteCalculatorsNotifier(),
);

class FavoriteCalculatorsNotifier extends StateNotifier<List<String>> {
  FavoriteCalculatorsNotifier() : super([]);

  void toggle(String calculatorId) {
    if (state.contains(calculatorId)) {
      state = state.where((id) => id != calculatorId).toList();
    } else {
      state = [...state, calculatorId];
    }
  }

  bool isFavorite(String calculatorId) => state.contains(calculatorId);
}
