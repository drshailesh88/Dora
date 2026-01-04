import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../theme.dart';
import '../../providers/gamification_provider.dart';

class ChallengesScreen extends ConsumerWidget {
  const ChallengesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final challenges = ref.watch(challengesProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Challenges'),
        backgroundColor: DoraColors.bgPrimary,
        elevation: 0,
      ),
      body: challenges.when(
        data: (data) => _buildChallengesList(data),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
      ),
    );
  }

  Widget _buildChallengesList(Map<String, dynamic> data) {
    final daily = data['daily'] as List? ?? [];
    final weekly = data['weekly'] as List? ?? [];
    final special = data['special'] as List? ?? [];

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSection('Daily Challenges', daily, Colors.blue),
          const SizedBox(height: 24),
          _buildSection('Weekly Challenges', weekly, Colors.purple),
          if (special.isNotEmpty) ...[
            const SizedBox(height: 24),
            _buildSection('Special Events', special, Colors.orange),
          ],
        ],
      ),
    );
  }

  Widget _buildSection(String title, List challenges, Color accentColor) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Container(
              width: 4,
              height: 20,
              decoration: BoxDecoration(
                color: accentColor,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            const SizedBox(width: 8),
            Text(
              title,
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
          ],
        ),
        const SizedBox(height: 12),
        ...challenges.map((c) => _buildChallengeCard(c, accentColor)),
        if (challenges.isEmpty)
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: DoraColors.bgSecondary,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Center(
              child: Text(
                'No active challenges',
                style: TextStyle(color: DoraColors.textSecondary),
              ),
            ),
          ),
      ],
    );
  }

  Widget _buildChallengeCard(Map<String, dynamic> challenge, Color accentColor) {
    final progress = challenge['progress'] ?? 0;
    final target = challenge['target'] ?? 1;
    final progressPercent = progress / target;
    final isCompleted = progress >= target;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isCompleted
            ? DoraColors.success.withOpacity(0.1)
            : DoraColors.bgSecondary,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isCompleted ? DoraColors.success : DoraColors.borderColor,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: accentColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  _getChallengeIcon(challenge['type'] ?? ''),
                  color: accentColor,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      challenge['title'] ?? 'Challenge',
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      challenge['description'] ?? '',
                      style: TextStyle(
                        color: DoraColors.textSecondary,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: isCompleted
                      ? DoraColors.success
                      : accentColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      isCompleted ? Icons.check : Icons.stars,
                      size: 14,
                      color: isCompleted ? Colors.white : accentColor,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      isCompleted ? 'Done!' : '+${challenge['points'] ?? 0}',
                      style: TextStyle(
                        color: isCompleted ? Colors.white : accentColor,
                        fontWeight: FontWeight.bold,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: progressPercent.clamp(0.0, 1.0),
                    backgroundColor: DoraColors.borderColor,
                    valueColor: AlwaysStoppedAnimation<Color>(
                      isCompleted ? DoraColors.success : accentColor,
                    ),
                    minHeight: 8,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Text(
                '$progress / $target',
                style: TextStyle(
                  color: DoraColors.textSecondary,
                  fontSize: 12,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
          if (challenge['expires_in'] != null) ...[
            const SizedBox(height: 8),
            Row(
              children: [
                Icon(
                  Icons.access_time,
                  size: 14,
                  color: DoraColors.textSecondary,
                ),
                const SizedBox(width: 4),
                Text(
                  'Expires in ${challenge['expires_in']}',
                  style: TextStyle(
                    color: DoraColors.textSecondary,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  IconData _getChallengeIcon(String type) {
    switch (type.toLowerCase()) {
      case 'query':
        return Icons.search;
      case 'learning':
        return Icons.school;
      case 'streak':
        return Icons.local_fire_department;
      case 'calculator':
        return Icons.calculate;
      case 'social':
        return Icons.people;
      default:
        return Icons.flag;
    }
  }
}
