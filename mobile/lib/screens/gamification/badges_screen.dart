import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../theme.dart';
import '../../providers/gamification_provider.dart';

class BadgesScreen extends ConsumerWidget {
  const BadgesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final badges = ref.watch(badgesProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Badges'),
        backgroundColor: DoraColors.bgPrimary,
        elevation: 0,
      ),
      body: badges.when(
        data: (data) => _buildBadgeGrid(data),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
      ),
    );
  }

  Widget _buildBadgeGrid(Map<String, dynamic> data) {
    final earnedBadges = data['earned'] as List? ?? [];
    final availableBadges = data['available'] as List? ?? [];

    return DefaultTabController(
      length: 2,
      child: Column(
        children: [
          TabBar(
            labelColor: DoraColors.primary,
            unselectedLabelColor: DoraColors.textSecondary,
            indicatorColor: DoraColors.primary,
            tabs: [
              Tab(text: 'Earned (${earnedBadges.length})'),
              Tab(text: 'Available (${availableBadges.length})'),
            ],
          ),
          Expanded(
            child: TabBarView(
              children: [
                _buildBadgeList(earnedBadges, earned: true),
                _buildBadgeList(availableBadges, earned: false),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBadgeList(List badges, {required bool earned}) {
    if (badges.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              earned ? Icons.military_tech : Icons.lock_outline,
              size: 64,
              color: DoraColors.textSecondary,
            ),
            const SizedBox(height: 16),
            Text(
              earned ? 'No badges earned yet' : 'All badges earned!',
              style: TextStyle(color: DoraColors.textSecondary),
            ),
          ],
        ),
      );
    }

    return GridView.builder(
      padding: const EdgeInsets.all(16),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 3,
        childAspectRatio: 0.8,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
      ),
      itemCount: badges.length,
      itemBuilder: (context, index) => _buildBadgeCard(badges[index], earned),
    );
  }

  Widget _buildBadgeCard(Map<String, dynamic> badge, bool earned) {
    final rarity = badge['rarity'] ?? 'common';
    final rarityColor = _getRarityColor(rarity);

    return InkWell(
      onTap: () {},
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: DoraColors.bgSecondary,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: earned ? rarityColor : DoraColors.borderColor,
            width: earned ? 2 : 1,
          ),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              badge['icon'] ?? '🏅',
              style: TextStyle(
                fontSize: 32,
                color: earned ? null : Colors.grey,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              badge['name'] ?? 'Badge',
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w500,
                color: earned ? DoraColors.textPrimary : DoraColors.textSecondary,
              ),
              textAlign: TextAlign.center,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 4),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: rarityColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                rarity.toUpperCase(),
                style: TextStyle(
                  fontSize: 8,
                  color: rarityColor,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _getRarityColor(String rarity) {
    switch (rarity.toLowerCase()) {
      case 'common':
        return Colors.grey;
      case 'uncommon':
        return Colors.green;
      case 'rare':
        return Colors.blue;
      case 'epic':
        return Colors.purple;
      case 'legendary':
        return Colors.orange;
      default:
        return Colors.grey;
    }
  }
}
