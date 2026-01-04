import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../theme.dart';
import '../models/medical_answer.dart';
import 'query_screen.dart';

class HistoryScreen extends ConsumerWidget {
  const HistoryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final answers = ref.watch(queryAnswersProvider);

    return Scaffold(
      backgroundColor: DoraColors.bgSecondary,
      appBar: AppBar(
        title: const Text('History'),
        actions: [
          if (answers.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.delete_sweep),
              onPressed: () {
                _showClearConfirmation(context, ref);
              },
            ),
        ],
      ),
      body: answers.isEmpty
          ? _buildEmptyState(context)
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: answers.length,
              itemBuilder: (context, index) {
                final answer = answers[answers.length - 1 - index];
                return Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: _buildHistoryItem(context, answer),
                );
              },
            ),
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.history,
            size: 64,
            color: DoraColors.textTertiary.withOpacity(0.5),
          ),
          const SizedBox(height: 16),
          Text(
            'No queries yet',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: DoraColors.textSecondary,
                ),
          ),
          const SizedBox(height: 8),
          Text(
            'Your query history will appear here',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: DoraColors.textTertiary,
                ),
          ),
        ],
      ),
    );
  }

  Widget _buildHistoryItem(BuildContext context, MedicalAnswer answer) {
    final confidenceColor = _getConfidenceColor(answer.confidenceLevel);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: DoraColors.bgPrimary,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: DoraColors.bgTertiary),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header row
          Row(
            children: [
              Text(
                _formatTime(answer.generatedAt),
                style: const TextStyle(
                  fontSize: 12,
                  color: DoraColors.textTertiary,
                ),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: confidenceColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  answer.confidence.toUpperCase(),
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w600,
                    color: confidenceColor,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Question
          Text(
            answer.question,
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w500,
              color: DoraColors.textPrimary,
            ),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 8),

          // Answer preview
          Text(
            answer.answer,
            style: const TextStyle(
              fontSize: 14,
              color: DoraColors.textSecondary,
            ),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 12),

          // Stats row
          Row(
            children: [
              Icon(
                Icons.format_quote,
                size: 14,
                color: DoraColors.textTertiary,
              ),
              const SizedBox(width: 4),
              Text(
                '${answer.citations.length} citations',
                style: const TextStyle(
                  fontSize: 12,
                  color: DoraColors.textTertiary,
                ),
              ),
              const SizedBox(width: 16),
              Icon(
                Icons.timer_outlined,
                size: 14,
                color: DoraColors.textTertiary,
              ),
              const SizedBox(width: 4),
              Text(
                '${answer.latencyMs}ms',
                style: const TextStyle(
                  fontSize: 12,
                  color: DoraColors.textTertiary,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Color _getConfidenceColor(ConfidenceLevel level) {
    switch (level) {
      case ConfidenceLevel.high:
        return DoraColors.success;
      case ConfidenceLevel.medium:
        return DoraColors.warning;
      case ConfidenceLevel.low:
        return DoraColors.error;
      case ConfidenceLevel.unknown:
        return DoraColors.textTertiary;
    }
  }

  String _formatTime(DateTime time) {
    final now = DateTime.now();
    final diff = now.difference(time);

    if (diff.inMinutes < 1) {
      return 'Just now';
    } else if (diff.inHours < 1) {
      return '${diff.inMinutes}m ago';
    } else if (diff.inDays < 1) {
      return '${diff.inHours}h ago';
    } else if (diff.inDays < 7) {
      return '${diff.inDays}d ago';
    } else {
      return '${time.month}/${time.day}';
    }
  }

  void _showClearConfirmation(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Clear History'),
        content: const Text('Are you sure you want to clear all query history?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              ref.read(queryAnswersProvider.notifier).state = [];
              Navigator.pop(context);
            },
            style: TextButton.styleFrom(foregroundColor: DoraColors.error),
            child: const Text('Clear'),
          ),
        ],
      ),
    );
  }
}
