import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../theme.dart';
import '../../providers/gamification_provider.dart';
import 'badges_screen.dart';
import 'leaderboard_screen.dart';
import 'challenges_screen.dart';

class GamificationHubScreen extends ConsumerWidget {
  const GamificationHubScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final stats = ref.watch(gamificationStatsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('My Progress'),
        backgroundColor: DoraColors.bgPrimary,
        elevation: 0,
      ),
      body: stats.when(
        data: (data) => _buildContent(context, data),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
      ),
    );
  }

  Widget _buildContent(BuildContext context, Map<String, dynamic> stats) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildLevelCard(stats),
          const SizedBox(height: 16),
          _buildPointsCard(stats),
          const SizedBox(height: 16),
          _buildStreakCard(stats),
          const SizedBox(height: 24),
          _buildQuickActions(context),
          const SizedBox(height: 24),
          _buildRecentBadges(stats),
          const SizedBox(height: 24),
          _buildDailyChallenges(stats),
        ],
      ),
    );
  }

  Widget _buildLevelCard(Map<String, dynamic> stats) {
    final level = stats['level'] ?? 1;
    final levelTitle = stats['level_title'] ?? 'Medical Student';
    final progress = (stats['progress_to_next'] ?? 0.0) / 100;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [DoraColors.primary, DoraColors.primary.withOpacity(0.8)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Container(
                width: 60,
                height: 60,
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(30),
                ),
                child: Center(
                  child: Text(
                    '$level',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      levelTitle,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Level $level',
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.8),
                        fontSize: 14,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          LinearProgressIndicator(
            value: progress,
            backgroundColor: Colors.white.withOpacity(0.2),
            valueColor: const AlwaysStoppedAnimation<Color>(Colors.white),
            borderRadius: BorderRadius.circular(4),
          ),
          const SizedBox(height: 8),
          Text(
            '${(progress * 100).toInt()}% to next level',
            style: TextStyle(
              color: Colors.white.withOpacity(0.8),
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPointsCard(Map<String, dynamic> stats) {
    final points = stats['total_points'] ?? 0;
    final todayPoints = stats['today_points'] ?? 0;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: DoraColors.bgSecondary,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: DoraColors.borderColor),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildStatItem(
            icon: Icons.stars_rounded,
            value: '$points',
            label: 'Total Points',
            color: Colors.amber,
          ),
          Container(width: 1, height: 40, color: DoraColors.borderColor),
          _buildStatItem(
            icon: Icons.today_rounded,
            value: '+$todayPoints',
            label: 'Today',
            color: DoraColors.success,
          ),
        ],
      ),
    );
  }

  Widget _buildStreakCard(Map<String, dynamic> stats) {
    final streak = stats['current_streak'] ?? 0;
    final longestStreak = stats['longest_streak'] ?? 0;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: DoraColors.bgSecondary,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: DoraColors.borderColor),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildStatItem(
            icon: Icons.local_fire_department_rounded,
            value: '$streak days',
            label: 'Current Streak',
            color: Colors.orange,
          ),
          Container(width: 1, height: 40, color: DoraColors.borderColor),
          _buildStatItem(
            icon: Icons.emoji_events_rounded,
            value: '$longestStreak days',
            label: 'Best Streak',
            color: Colors.purple,
          ),
        ],
      ),
    );
  }

  Widget _buildStatItem({
    required IconData icon,
    required String value,
    required String label,
    required Color color,
  }) {
    return Column(
      children: [
        Icon(icon, color: color, size: 28),
        const SizedBox(height: 8),
        Text(
          value,
          style: const TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: DoraColors.textSecondary,
          ),
        ),
      ],
    );
  }

  Widget _buildQuickActions(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _buildActionButton(
            context,
            icon: Icons.military_tech_rounded,
            label: 'Badges',
            onTap: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const BadgesScreen()),
            ),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _buildActionButton(
            context,
            icon: Icons.leaderboard_rounded,
            label: 'Leaderboard',
            onTap: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const LeaderboardScreen()),
            ),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _buildActionButton(
            context,
            icon: Icons.flag_rounded,
            label: 'Challenges',
            onTap: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const ChallengesScreen()),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildActionButton(
    BuildContext context, {
    required IconData icon,
    required String label,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 16),
        decoration: BoxDecoration(
          color: DoraColors.bgSecondary,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: DoraColors.borderColor),
        ),
        child: Column(
          children: [
            Icon(icon, color: DoraColors.primary, size: 28),
            const SizedBox(height: 8),
            Text(label, style: const TextStyle(fontSize: 12)),
          ],
        ),
      ),
    );
  }

  Widget _buildRecentBadges(Map<String, dynamic> stats) {
    final badges = (stats['recent_badges'] as List?)?.take(4).toList() ?? [];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Recent Badges',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            TextButton(
              onPressed: () {},
              child: Text('See All', style: TextStyle(color: DoraColors.primary)),
            ),
          ],
        ),
        const SizedBox(height: 12),
        if (badges.isEmpty)
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: DoraColors.bgSecondary,
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Center(
              child: Text('Complete activities to earn badges!'),
            ),
          )
        else
          Row(
            children: badges.map((badge) => _buildBadgeItem(badge)).toList(),
          ),
      ],
    );
  }

  Widget _buildBadgeItem(Map<String, dynamic> badge) {
    return Expanded(
      child: Container(
        margin: const EdgeInsets.only(right: 8),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: DoraColors.bgSecondary,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          children: [
            Text(badge['icon'] ?? '🏅', style: const TextStyle(fontSize: 32)),
            const SizedBox(height: 4),
            Text(
              badge['name'] ?? 'Badge',
              style: const TextStyle(fontSize: 10),
              textAlign: TextAlign.center,
              maxLines: 2,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDailyChallenges(Map<String, dynamic> stats) {
    final challenges = (stats['daily_challenges'] as List?)?.take(3).toList() ?? [];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Daily Challenges',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 12),
        ...challenges.map((c) => _buildChallengeItem(c)),
        if (challenges.isEmpty)
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: DoraColors.bgSecondary,
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Center(child: Text('No active challenges')),
          ),
      ],
    );
  }

  Widget _buildChallengeItem(Map<String, dynamic> challenge) {
    final progress = (challenge['progress'] ?? 0) / (challenge['target'] ?? 1);

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: DoraColors.bgSecondary,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: DoraColors.primary.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(Icons.flag, color: DoraColors.primary),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  challenge['title'] ?? 'Challenge',
                  style: const TextStyle(fontWeight: FontWeight.w500),
                ),
                const SizedBox(height: 4),
                LinearProgressIndicator(
                  value: progress,
                  backgroundColor: DoraColors.borderColor,
                  valueColor: AlwaysStoppedAnimation<Color>(DoraColors.primary),
                  borderRadius: BorderRadius.circular(2),
                ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          Text(
            '+${challenge['points'] ?? 0}',
            style: TextStyle(
              color: DoraColors.primary,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}
