import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../theme.dart';
import '../../providers/engagement_provider.dart';

class MorningBriefingScreen extends ConsumerWidget {
  const MorningBriefingScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final briefing = ref.watch(morningBriefingProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Morning Briefing'),
        backgroundColor: DoraColors.bgPrimary,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.refresh(morningBriefingProvider),
          ),
        ],
      ),
      body: briefing.when(
        data: (data) => _buildBriefing(context, data),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
      ),
    );
  }

  Widget _buildBriefing(BuildContext context, Map<String, dynamic> data) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildGreeting(data),
          const SizedBox(height: 24),
          _buildClinicalPearl(data['clinical_pearl'] ?? {}),
          const SizedBox(height: 24),
          _buildTodayPatients(data['patients'] ?? []),
          const SizedBox(height: 24),
          _buildTrendingQueries(data['trending'] ?? []),
          const SizedBox(height: 24),
          _buildLearningStreak(data),
        ],
      ),
    );
  }

  Widget _buildGreeting(Map<String, dynamic> data) {
    final hour = DateTime.now().hour;
    String greeting;
    IconData icon;

    if (hour < 12) {
      greeting = 'Good Morning';
      icon = Icons.wb_sunny;
    } else if (hour < 17) {
      greeting = 'Good Afternoon';
      icon = Icons.wb_cloudy;
    } else {
      greeting = 'Good Evening';
      icon = Icons.nights_stay;
    }

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
      child: Row(
        children: [
          Icon(icon, color: Colors.white, size: 48),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  greeting,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'You have ${data['patient_count'] ?? 0} patients today',
                  style: TextStyle(color: Colors.white.withOpacity(0.9)),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildClinicalPearl(Map<String, dynamic> pearl) {
    if (pearl.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Row(
          children: [
            Icon(Icons.lightbulb, color: Colors.amber, size: 20),
            SizedBox(width: 8),
            Text(
              'Clinical Pearl of the Day',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.amber.withOpacity(0.1),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.amber.withOpacity(0.3)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                pearl['title'] ?? 'Clinical Pearl',
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Text(
                pearl['content'] ?? '',
                style: TextStyle(color: DoraColors.textSecondary),
              ),
              if (pearl['source'] != null) ...[
                const SizedBox(height: 8),
                Text(
                  'Source: ${pearl['source']}',
                  style: TextStyle(
                    fontSize: 12,
                    color: DoraColors.textSecondary,
                    fontStyle: FontStyle.italic,
                  ),
                ),
              ],
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildTodayPatients(List patients) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              "Today's Patients",
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            TextButton(
              onPressed: () {},
              child: const Text('View All'),
            ),
          ],
        ),
        const SizedBox(height: 12),
        if (patients.isEmpty)
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: DoraColors.bgSecondary,
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Center(child: Text('No appointments today')),
          )
        else
          ...patients.take(3).map((p) => _buildPatientCard(p)),
      ],
    );
  }

  Widget _buildPatientCard(Map<String, dynamic> patient) {
    final hasAlert = patient['has_alert'] == true;

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: DoraColors.bgSecondary,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: hasAlert ? DoraColors.error : DoraColors.borderColor,
        ),
      ),
      child: Row(
        children: [
          CircleAvatar(
            backgroundColor: DoraColors.primary.withOpacity(0.2),
            child: Text(
              patient['name']?.toString().substring(0, 1).toUpperCase() ?? '?',
              style: TextStyle(color: DoraColors.primary),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      patient['name'] ?? 'Patient',
                      style: const TextStyle(fontWeight: FontWeight.w500),
                    ),
                    if (hasAlert) ...[
                      const SizedBox(width: 8),
                      Icon(Icons.warning, color: DoraColors.error, size: 16),
                    ],
                  ],
                ),
                Text(
                  patient['reason'] ?? '',
                  style: TextStyle(
                    color: DoraColors.textSecondary,
                    fontSize: 13,
                  ),
                ),
              ],
            ),
          ),
          Text(
            patient['time'] ?? '',
            style: TextStyle(color: DoraColors.primary),
          ),
        ],
      ),
    );
  }

  Widget _buildTrendingQueries(List trending) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Trending in Your Specialty',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: trending.take(6).map((q) => _buildTrendingChip(q)).toList(),
        ),
      ],
    );
  }

  Widget _buildTrendingChip(Map<String, dynamic> query) {
    return InkWell(
      onTap: () {},
      borderRadius: BorderRadius.circular(20),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: DoraColors.bgSecondary,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: DoraColors.borderColor),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.trending_up, size: 14, color: DoraColors.success),
            const SizedBox(width: 4),
            Text(
              query['query'] ?? '',
              style: const TextStyle(fontSize: 13),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLearningStreak(Map<String, dynamic> data) {
    final streak = data['streak'] ?? 0;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: DoraColors.bgSecondary,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Icon(
            Icons.local_fire_department,
            color: streak > 0 ? Colors.orange : DoraColors.textSecondary,
            size: 32,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '$streak Day Streak',
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
                Text(
                  streak > 0
                      ? 'Keep it going! Ask a question today.'
                      : 'Start your streak today!',
                  style: TextStyle(
                    color: DoraColors.textSecondary,
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
}
