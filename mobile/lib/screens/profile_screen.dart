import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../theme.dart';
import '../providers/auth_provider.dart';
import 'gamification/gamification_hub_screen.dart';
import 'analytics/practice_analytics_screen.dart';
import 'learning/learning_dashboard.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Profile'),
        backgroundColor: DoraColors.bgPrimary,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.edit),
            onPressed: () => _editProfile(context),
          ),
        ],
      ),
      body: user.when(
        data: (data) => _buildProfile(context, ref, data),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
      ),
    );
  }

  Widget _buildProfile(BuildContext context, WidgetRef ref, Map<String, dynamic> user) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          _buildProfileHeader(user),
          const SizedBox(height: 24),
          _buildStatsRow(user),
          const SizedBox(height: 24),
          _buildMenuSection(context),
          const SizedBox(height: 24),
          _buildAccountSection(context, ref),
        ],
      ),
    );
  }

  Widget _buildProfileHeader(Map<String, dynamic> user) {
    return Column(
      children: [
        CircleAvatar(
          radius: 50,
          backgroundColor: DoraColors.primary.withOpacity(0.2),
          child: Text(
            user['name']?.toString().substring(0, 1).toUpperCase() ?? 'D',
            style: TextStyle(
              fontSize: 40,
              fontWeight: FontWeight.bold,
              color: DoraColors.primary,
            ),
          ),
        ),
        const SizedBox(height: 16),
        Text(
          user['name'] ?? 'Doctor',
          style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 4),
        Text(
          user['specialty'] ?? 'General Medicine',
          style: TextStyle(color: DoraColors.textSecondary, fontSize: 16),
        ),
        const SizedBox(height: 4),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.badge, size: 14, color: DoraColors.textSecondary),
            const SizedBox(width: 4),
            Text(
              user['license_number'] ?? 'MCI-XXXXX',
              style: TextStyle(color: DoraColors.textSecondary, fontSize: 12),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildStatsRow(Map<String, dynamic> user) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: DoraColors.bgSecondary,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildStatItem(
            value: '${user['total_queries'] ?? 0}',
            label: 'Queries',
          ),
          Container(width: 1, height: 40, color: DoraColors.borderColor),
          _buildStatItem(
            value: '${user['streak'] ?? 0}',
            label: 'Day Streak',
          ),
          Container(width: 1, height: 40, color: DoraColors.borderColor),
          _buildStatItem(
            value: '${user['cme_credits'] ?? 0}',
            label: 'CME Credits',
          ),
        ],
      ),
    );
  }

  Widget _buildStatItem({required String value, required String label}) {
    return Column(
      children: [
        Text(
          value,
          style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
        ),
        Text(
          label,
          style: TextStyle(color: DoraColors.textSecondary, fontSize: 12),
        ),
      ],
    );
  }

  Widget _buildMenuSection(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'My Dora',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 12),
        _buildMenuItem(
          context,
          icon: Icons.emoji_events,
          title: 'Achievements & Progress',
          subtitle: 'Badges, levels, and streaks',
          onTap: () => Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const GamificationHubScreen()),
          ),
        ),
        _buildMenuItem(
          context,
          icon: Icons.analytics,
          title: 'Practice Analytics',
          subtitle: 'Query patterns and insights',
          onTap: () => Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const PracticeAnalyticsScreen()),
          ),
        ),
        _buildMenuItem(
          context,
          icon: Icons.school,
          title: 'Learning Dashboard',
          subtitle: 'CME credits and courses',
          onTap: () => Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const LearningDashboard()),
          ),
        ),
        _buildMenuItem(
          context,
          icon: Icons.history,
          title: 'Query History',
          subtitle: 'Past queries and answers',
          onTap: () {},
        ),
        _buildMenuItem(
          context,
          icon: Icons.bookmark,
          title: 'Saved Items',
          subtitle: 'Bookmarked articles and answers',
          onTap: () {},
        ),
      ],
    );
  }

  Widget _buildAccountSection(BuildContext context, WidgetRef ref) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Account',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 12),
        _buildMenuItem(
          context,
          icon: Icons.credit_card,
          title: 'Subscription',
          subtitle: 'Manage your plan',
          onTap: () {},
        ),
        _buildMenuItem(
          context,
          icon: Icons.notifications,
          title: 'Notifications',
          subtitle: 'Alerts and briefing settings',
          onTap: () {},
        ),
        _buildMenuItem(
          context,
          icon: Icons.security,
          title: 'Privacy & Security',
          subtitle: 'Password and data settings',
          onTap: () {},
        ),
        _buildMenuItem(
          context,
          icon: Icons.help,
          title: 'Help & Support',
          subtitle: 'FAQ and contact us',
          onTap: () {},
        ),
        const SizedBox(height: 16),
        SizedBox(
          width: double.infinity,
          child: OutlinedButton.icon(
            onPressed: () => _logout(context, ref),
            icon: const Icon(Icons.logout, color: Colors.red),
            label: const Text('Sign Out', style: TextStyle(color: Colors.red)),
            style: OutlinedButton.styleFrom(
              side: const BorderSide(color: Colors.red),
              padding: const EdgeInsets.symmetric(vertical: 12),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildMenuItem(
    BuildContext context, {
    required IconData icon,
    required String title,
    required String subtitle,
    required VoidCallback onTap,
  }) {
    return ListTile(
      contentPadding: EdgeInsets.zero,
      leading: Container(
        width: 40,
        height: 40,
        decoration: BoxDecoration(
          color: DoraColors.primary.withOpacity(0.1),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Icon(icon, color: DoraColors.primary),
      ),
      title: Text(title),
      subtitle: Text(
        subtitle,
        style: TextStyle(color: DoraColors.textSecondary, fontSize: 12),
      ),
      trailing: const Icon(Icons.chevron_right),
      onTap: onTap,
    );
  }

  void _editProfile(BuildContext context) {
    // Navigate to edit profile screen
  }

  void _logout(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Sign Out'),
        content: const Text('Are you sure you want to sign out?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              ref.read(authProvider.notifier).logout();
            },
            child: const Text('Sign Out', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }
}
