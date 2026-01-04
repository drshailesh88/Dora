import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_service.dart';

/// Provider for search suggestions
final searchSuggestionsProvider = FutureProvider.family<List<Map<String, dynamic>>, String>(
  (ref, query) async {
    if (query.length < 2) return [];

    final api = ref.watch(apiServiceProvider);
    final result = await api.get('/search/suggestions?q=${Uri.encodeComponent(query)}');
    return List<Map<String, dynamic>>.from(result['suggestions'] ?? []);
  },
);

/// Provider for recent searches
final recentSearchesProvider = StateNotifierProvider<RecentSearchesNotifier, AsyncValue<List<String>>>(
  (ref) => RecentSearchesNotifier(ref),
);

class RecentSearchesNotifier extends StateNotifier<AsyncValue<List<String>>> {
  final Ref ref;

  RecentSearchesNotifier(this.ref) : super(const AsyncValue.loading()) {
    _load();
  }

  Future<void> _load() async {
    try {
      final api = ref.read(apiServiceProvider);
      final result = await api.get('/search/recent');
      state = AsyncValue.data(List<String>.from(result['searches'] ?? []));
    } catch (e) {
      state = AsyncValue.data([]);
    }
  }

  Future<void> add(String search) async {
    final current = state.valueOrNull ?? [];
    if (current.contains(search)) {
      // Move to top
      state = AsyncValue.data([search, ...current.where((s) => s != search)]);
    } else {
      state = AsyncValue.data([search, ...current.take(19)]);
    }
    // TODO: Persist to API
  }

  Future<void> clear() async {
    state = const AsyncValue.data([]);
    // TODO: Clear on API
  }
}

/// Provider for trending searches
final trendingSearchesProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  final result = await api.get('/search/trending');
  return List<Map<String, dynamic>>.from(result['trending'] ?? []);
});

/// Provider for drug autocomplete
final drugAutocompleteProvider = FutureProvider.family<List<Map<String, dynamic>>, String>(
  (ref, query) async {
    if (query.length < 2) return [];

    final api = ref.watch(apiServiceProvider);
    final result = await api.get('/drugs/autocomplete?q=${Uri.encodeComponent(query)}');
    return List<Map<String, dynamic>>.from(result['drugs'] ?? []);
  },
);

/// Provider for calculator search
final calculatorSearchProvider = FutureProvider.family<List<Map<String, dynamic>>, String>(
  (ref, query) async {
    if (query.isEmpty) return [];

    final api = ref.watch(apiServiceProvider);
    final result = await api.get('/calculators/search?q=${Uri.encodeComponent(query)}');
    return List<Map<String, dynamic>>.from(result['calculators'] ?? []);
  },
);
