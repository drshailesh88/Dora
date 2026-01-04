import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../theme.dart';
import '../services/api_client.dart';
import '../models/drug_interaction.dart';
import '../widgets/drug_interaction_card.dart';

/// Provider for drug check state
final drugCheckLoadingProvider = StateProvider<bool>((ref) => false);
final drugCheckResultProvider = StateProvider<DrugInteractionResult?>((ref) => null);

class DrugsScreen extends ConsumerStatefulWidget {
  const DrugsScreen({super.key});

  @override
  ConsumerState<DrugsScreen> createState() => _DrugsScreenState();
}

class _DrugsScreenState extends ConsumerState<DrugsScreen> {
  final List<TextEditingController> _controllers = [
    TextEditingController(),
    TextEditingController(),
  ];

  @override
  void dispose() {
    for (final c in _controllers) {
      c.dispose();
    }
    super.dispose();
  }

  void _addDrugField() {
    setState(() {
      _controllers.add(TextEditingController());
    });
  }

  void _removeDrugField(int index) {
    if (_controllers.length > 2) {
      setState(() {
        _controllers[index].dispose();
        _controllers.removeAt(index);
      });
    }
  }

  Future<void> _checkInteractions() async {
    final drugs = _controllers
        .map((c) => c.text.trim())
        .where((t) => t.isNotEmpty)
        .toList();

    if (drugs.length < 2) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please enter at least 2 drugs'),
          backgroundColor: DoraColors.warning,
        ),
      );
      return;
    }

    ref.read(drugCheckLoadingProvider.notifier).state = true;

    final client = ref.read(apiClientProvider);
    final result = await client.checkDrugInteractions(drugs: drugs);

    ref.read(drugCheckLoadingProvider.notifier).state = false;
    ref.read(drugCheckResultProvider.notifier).state = result;
  }

  @override
  Widget build(BuildContext context) {
    final isLoading = ref.watch(drugCheckLoadingProvider);
    final result = ref.watch(drugCheckResultProvider);

    return Scaffold(
      backgroundColor: DoraColors.bgSecondary,
      appBar: AppBar(
        title: const Text('Drug Interactions'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Drug inputs card
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: DoraColors.bgPrimary,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'ENTER MEDICATIONS',
                    style: Theme.of(context).textTheme.labelSmall,
                  ),
                  const SizedBox(height: 16),

                  // Drug input fields
                  ...List.generate(_controllers.length, (index) {
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: Row(
                        children: [
                          Expanded(
                            child: TextField(
                              controller: _controllers[index],
                              decoration: InputDecoration(
                                labelText: 'Drug ${index + 1}',
                                hintText: 'Enter drug name',
                              ),
                              textCapitalization: TextCapitalization.words,
                            ),
                          ),
                          if (index >= 2) ...[
                            const SizedBox(width: 8),
                            IconButton(
                              icon: const Icon(Icons.remove_circle_outline),
                              color: DoraColors.error,
                              onPressed: () => _removeDrugField(index),
                            ),
                          ],
                        ],
                      ),
                    );
                  }),

                  // Add drug button
                  TextButton.icon(
                    onPressed: _addDrugField,
                    icon: const Icon(Icons.add),
                    label: const Text('Add another drug'),
                  ),
                  const SizedBox(height: 16),

                  // Check button
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: isLoading ? null : _checkInteractions,
                      icon: isLoading
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                valueColor: AlwaysStoppedAnimation(Colors.white),
                              ),
                            )
                          : const Icon(Icons.verified_user),
                      label: Text(isLoading ? 'Checking...' : 'Check Interactions'),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Severity guide
            _buildSeverityGuide(),
            const SizedBox(height: 16),

            // Results
            if (result != null) _buildResults(result),
          ],
        ),
      ),
    );
  }

  Widget _buildSeverityGuide() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: DoraColors.bgPrimary,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'SEVERITY GUIDE',
            style: Theme.of(context).textTheme.labelSmall,
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 16,
            runSpacing: 8,
            children: [
              _buildSeverityLegend('Contraindicated', DoraColors.contraindicated),
              _buildSeverityLegend('Severe', DoraColors.severe),
              _buildSeverityLegend('Moderate', DoraColors.moderate),
              _buildSeverityLegend('Mild', DoraColors.mild),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSeverityLegend(String label, Color color) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(3),
          ),
        ),
        const SizedBox(width: 6),
        Text(
          label,
          style: const TextStyle(
            fontSize: 12,
            color: DoraColors.textSecondary,
          ),
        ),
      ],
    );
  }

  Widget _buildResults(DrugInteractionResult result) {
    if (!result.success) {
      return Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: DoraColors.error.withOpacity(0.1),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          children: [
            const Icon(Icons.error_outline, color: DoraColors.error),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                result.error ?? 'Failed to check interactions',
                style: const TextStyle(color: DoraColors.error),
              ),
            ),
          ],
        ),
      );
    }

    if (!result.hasInteractions) {
      return Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: DoraColors.success.withOpacity(0.1),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          children: [
            const Icon(Icons.check_circle, color: DoraColors.success, size: 28),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'No interactions found',
                    style: TextStyle(
                      color: DoraColors.success,
                      fontWeight: FontWeight.w600,
                      fontSize: 16,
                    ),
                  ),
                  Text(
                    'These medications appear safe to use together',
                    style: TextStyle(
                      color: DoraColors.success.withOpacity(0.8),
                      fontSize: 13,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'INTERACTIONS FOUND',
          style: Theme.of(context).textTheme.labelSmall,
        ),
        const SizedBox(height: 12),
        ...result.interactions.map((interaction) {
          return Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: DrugInteractionCard(interaction: interaction),
          );
        }),
      ],
    );
  }
}
