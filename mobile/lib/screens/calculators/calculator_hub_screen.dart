import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../theme.dart';
import '../../providers/calculator_provider.dart';
import 'calculator_detail_screen.dart';

class CalculatorHubScreen extends ConsumerStatefulWidget {
  const CalculatorHubScreen({super.key});

  @override
  ConsumerState<CalculatorHubScreen> createState() => _CalculatorHubScreenState();
}

class _CalculatorHubScreenState extends ConsumerState<CalculatorHubScreen> {
  String _searchQuery = '';
  String _selectedCategory = 'all';

  final List<Map<String, dynamic>> _categories = [
    {'id': 'all', 'name': 'All', 'icon': Icons.apps},
    {'id': 'cardio', 'name': 'Cardiovascular', 'icon': Icons.favorite},
    {'id': 'renal', 'name': 'Renal', 'icon': Icons.water_drop},
    {'id': 'hepatic', 'name': 'Hepatic', 'icon': Icons.healing},
    {'id': 'pulm', 'name': 'Pulmonary', 'icon': Icons.air},
    {'id': 'neuro', 'name': 'Neurology', 'icon': Icons.psychology},
    {'id': 'general', 'name': 'General', 'icon': Icons.calculate},
  ];

  @override
  Widget build(BuildContext context) {
    final calculators = ref.watch(calculatorsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Medical Calculators'),
        backgroundColor: DoraColors.bgPrimary,
        elevation: 0,
      ),
      body: Column(
        children: [
          _buildSearchBar(),
          _buildCategoryFilter(),
          Expanded(
            child: calculators.when(
              data: (data) => _buildCalculatorList(data),
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(child: Text('Error: $e')),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSearchBar() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: TextField(
        onChanged: (value) => setState(() => _searchQuery = value),
        decoration: InputDecoration(
          hintText: 'Search calculators...',
          prefixIcon: const Icon(Icons.search),
          filled: true,
          fillColor: DoraColors.bgSecondary,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide.none,
          ),
          contentPadding: const EdgeInsets.symmetric(horizontal: 16),
        ),
      ),
    );
  }

  Widget _buildCategoryFilter() {
    return SizedBox(
      height: 44,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        itemCount: _categories.length,
        itemBuilder: (context, index) {
          final cat = _categories[index];
          final isSelected = _selectedCategory == cat['id'];

          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: FilterChip(
              selected: isSelected,
              label: Text(cat['name']),
              avatar: Icon(
                cat['icon'],
                size: 18,
                color: isSelected ? Colors.white : DoraColors.textSecondary,
              ),
              selectedColor: DoraColors.primary,
              backgroundColor: DoraColors.bgSecondary,
              labelStyle: TextStyle(
                color: isSelected ? Colors.white : DoraColors.textPrimary,
              ),
              onSelected: (_) => setState(() => _selectedCategory = cat['id']),
            ),
          );
        },
      ),
    );
  }

  Widget _buildCalculatorList(List<Map<String, dynamic>> calculators) {
    var filtered = calculators.where((c) {
      final matchesSearch = _searchQuery.isEmpty ||
          c['name'].toString().toLowerCase().contains(_searchQuery.toLowerCase());
      final matchesCategory = _selectedCategory == 'all' ||
          c['category'] == _selectedCategory;
      return matchesSearch && matchesCategory;
    }).toList();

    if (filtered.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.search_off, size: 64, color: DoraColors.textSecondary),
            const SizedBox(height: 16),
            Text(
              'No calculators found',
              style: TextStyle(color: DoraColors.textSecondary),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: filtered.length,
      itemBuilder: (context, index) => _buildCalculatorCard(filtered[index]),
    );
  }

  Widget _buildCalculatorCard(Map<String, dynamic> calculator) {
    return InkWell(
      onTap: () => Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => CalculatorDetailScreen(calculator: calculator),
        ),
      ),
      borderRadius: BorderRadius.circular(12),
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: DoraColors.bgSecondary,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: DoraColors.borderColor),
        ),
        child: Row(
          children: [
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: _getCategoryColor(calculator['category']).withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(
                _getCategoryIcon(calculator['category']),
                color: _getCategoryColor(calculator['category']),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    calculator['name'] ?? 'Calculator',
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    calculator['description'] ?? '',
                    style: TextStyle(
                      color: DoraColors.textSecondary,
                      fontSize: 13,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
            const Icon(Icons.chevron_right),
          ],
        ),
      ),
    );
  }

  Color _getCategoryColor(String? category) {
    switch (category) {
      case 'cardio':
        return Colors.red;
      case 'renal':
        return Colors.blue;
      case 'hepatic':
        return Colors.green;
      case 'pulm':
        return Colors.cyan;
      case 'neuro':
        return Colors.purple;
      default:
        return DoraColors.primary;
    }
  }

  IconData _getCategoryIcon(String? category) {
    switch (category) {
      case 'cardio':
        return Icons.favorite;
      case 'renal':
        return Icons.water_drop;
      case 'hepatic':
        return Icons.healing;
      case 'pulm':
        return Icons.air;
      case 'neuro':
        return Icons.psychology;
      default:
        return Icons.calculate;
    }
  }
}
