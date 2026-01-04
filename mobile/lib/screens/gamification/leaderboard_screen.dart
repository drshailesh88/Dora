import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../theme.dart';
import '../../providers/gamification_provider.dart';

class LeaderboardScreen extends ConsumerStatefulWidget {
  const LeaderboardScreen({super.key});

  @override
  ConsumerState<LeaderboardScreen> createState() => _LeaderboardScreenState();
}

class _LeaderboardScreenState extends ConsumerState<LeaderboardScreen> {
  String _period = 'week';
  String _scope = 'global';

  @override
  Widget build(BuildContext context) {
    final leaderboard = ref.watch(leaderboardProvider(_period, _scope));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Leaderboard'),
        backgroundColor: DoraColors.bgPrimary,
        elevation: 0,
      ),
      body: Column(
        children: [
          _buildFilters(),
          Expanded(
            child: leaderboard.when(
              data: (data) => _buildLeaderboard(data),
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(child: Text('Error: $e')),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilters() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          Expanded(
            child: _buildDropdown(
              value: _period,
              items: const ['week', 'month', 'all_time'],
              labels: const ['This Week', 'This Month', 'All Time'],
              onChanged: (v) => setState(() => _period = v!),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: _buildDropdown(
              value: _scope,
              items: const ['global', 'specialty', 'team'],
              labels: const ['Global', 'My Specialty', 'My Team'],
              onChanged: (v) => setState(() => _scope = v!),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDropdown({
    required String value,
    required List<String> items,
    required List<String> labels,
    required ValueChanged<String?> onChanged,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12),
      decoration: BoxDecoration(
        color: DoraColors.bgSecondary,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: DoraColors.borderColor),
      ),
      child: DropdownButton<String>(
        value: value,
        isExpanded: true,
        underline: const SizedBox(),
        items: List.generate(
          items.length,
          (i) => DropdownMenuItem(value: items[i], child: Text(labels[i])),
        ),
        onChanged: onChanged,
      ),
    );
  }

  Widget _buildLeaderboard(Map<String, dynamic> data) {
    final rankings = data['rankings'] as List? ?? [];
    final userRank = data['user_rank'] as int?;

    return Column(
      children: [
        if (rankings.length >= 3) _buildTopThree(rankings.take(3).toList()),
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: rankings.length > 3 ? rankings.length - 3 : 0,
            itemBuilder: (context, index) =>
                _buildRankItem(rankings[index + 3], index + 4),
          ),
        ),
        if (userRank != null) _buildUserRank(data),
      ],
    );
  }

  Widget _buildTopThree(List rankings) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 24),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          if (rankings.length > 1)
            _buildPodiumItem(rankings[1], 2, height: 100),
          const SizedBox(width: 12),
          if (rankings.isNotEmpty)
            _buildPodiumItem(rankings[0], 1, height: 130),
          const SizedBox(width: 12),
          if (rankings.length > 2)
            _buildPodiumItem(rankings[2], 3, height: 80),
        ],
      ),
    );
  }

  Widget _buildPodiumItem(Map<String, dynamic> user, int rank, {required double height}) {
    final colors = [Colors.amber, Colors.grey.shade400, Colors.brown.shade400];
    final medals = ['🥇', '🥈', '🥉'];

    return Column(
      children: [
        Text(medals[rank - 1], style: const TextStyle(fontSize: 32)),
        const SizedBox(height: 8),
        CircleAvatar(
          radius: 24,
          backgroundColor: colors[rank - 1],
          child: Text(
            user['name']?.toString().substring(0, 1).toUpperCase() ?? '?',
            style: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.bold,
              fontSize: 20,
            ),
          ),
        ),
        const SizedBox(height: 8),
        SizedBox(
          width: 80,
          child: Text(
            user['name'] ?? 'Anonymous',
            style: const TextStyle(fontWeight: FontWeight.w500),
            textAlign: TextAlign.center,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ),
        Text(
          '${user['points'] ?? 0} pts',
          style: TextStyle(
            color: DoraColors.textSecondary,
            fontSize: 12,
          ),
        ),
        const SizedBox(height: 8),
        Container(
          width: 80,
          height: height,
          decoration: BoxDecoration(
            color: colors[rank - 1].withOpacity(0.3),
            borderRadius: const BorderRadius.vertical(top: Radius.circular(8)),
          ),
          child: Center(
            child: Text(
              '#$rank',
              style: TextStyle(
                color: colors[rank - 1],
                fontWeight: FontWeight.bold,
                fontSize: 18,
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildRankItem(Map<String, dynamic> user, int rank) {
    final isCurrentUser = user['is_current_user'] == true;

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isCurrentUser
            ? DoraColors.primary.withOpacity(0.1)
            : DoraColors.bgSecondary,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isCurrentUser ? DoraColors.primary : DoraColors.borderColor,
        ),
      ),
      child: Row(
        children: [
          SizedBox(
            width: 32,
            child: Text(
              '#$rank',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                color: DoraColors.textSecondary,
              ),
            ),
          ),
          CircleAvatar(
            radius: 20,
            backgroundColor: DoraColors.primary.withOpacity(0.2),
            child: Text(
              user['name']?.toString().substring(0, 1).toUpperCase() ?? '?',
              style: TextStyle(
                color: DoraColors.primary,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  user['name'] ?? 'Anonymous',
                  style: const TextStyle(fontWeight: FontWeight.w500),
                ),
                Text(
                  user['specialty'] ?? '',
                  style: TextStyle(
                    color: DoraColors.textSecondary,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
          Text(
            '${user['points'] ?? 0}',
            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
          ),
          const SizedBox(width: 4),
          Text(
            'pts',
            style: TextStyle(color: DoraColors.textSecondary, fontSize: 12),
          ),
        ],
      ),
    );
  }

  Widget _buildUserRank(Map<String, dynamic> data) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: DoraColors.primary.withOpacity(0.1),
        border: Border(
          top: BorderSide(color: DoraColors.borderColor),
        ),
      ),
      child: Row(
        children: [
          Text(
            'Your Rank: #${data['user_rank']}',
            style: const TextStyle(fontWeight: FontWeight.bold),
          ),
          const Spacer(),
          Text(
            '${data['user_points'] ?? 0} points',
            style: TextStyle(color: DoraColors.primary),
          ),
        ],
      ),
    );
  }
}
