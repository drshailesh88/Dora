import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../theme.dart';
import '../../providers/analytics_provider.dart';

class PracticeAnalyticsScreen extends ConsumerStatefulWidget {
  const PracticeAnalyticsScreen({super.key});

  @override
  ConsumerState<PracticeAnalyticsScreen> createState() => _PracticeAnalyticsScreenState();
}

class _PracticeAnalyticsScreenState extends ConsumerState<PracticeAnalyticsScreen> {
  String _period = 'week';

  @override
  Widget build(BuildContext context) {
    final analytics = ref.watch(practiceAnalyticsProvider(_period));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Practice Analytics'),
        backgroundColor: DoraColors.bgPrimary,
        elevation: 0,
        actions: [
          PopupMenuButton<String>(
            icon: const Icon(Icons.calendar_today),
            onSelected: (value) => setState(() => _period = value),
            itemBuilder: (context) => [
              const PopupMenuItem(value: 'week', child: Text('This Week')),
              const PopupMenuItem(value: 'month', child: Text('This Month')),
              const PopupMenuItem(value: 'quarter', child: Text('This Quarter')),
              const PopupMenuItem(value: 'year', child: Text('This Year')),
            ],
          ),
        ],
      ),
      body: analytics.when(
        data: (data) => _buildAnalytics(data),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
      ),
    );
  }

  Widget _buildAnalytics(Map<String, dynamic> data) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSummaryCards(data),
          const SizedBox(height: 24),
          _buildQueryTrends(data['query_trends'] ?? []),
          const SizedBox(height: 24),
          _buildTopTopics(data['top_topics'] ?? []),
          const SizedBox(height: 24),
          _buildPrescriptionStats(data['prescriptions'] ?? {}),
          const SizedBox(height: 24),
          _buildLearningProgress(data['learning'] ?? {}),
        ],
      ),
    );
  }

  Widget _buildSummaryCards(Map<String, dynamic> data) {
    return GridView.count(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisCount: 2,
      mainAxisSpacing: 12,
      crossAxisSpacing: 12,
      childAspectRatio: 1.5,
      children: [
        _buildStatCard(
          title: 'Queries',
          value: '${data['total_queries'] ?? 0}',
          change: data['queries_change'],
          icon: Icons.search,
          color: Colors.blue,
        ),
        _buildStatCard(
          title: 'Prescriptions',
          value: '${data['total_prescriptions'] ?? 0}',
          change: data['prescriptions_change'],
          icon: Icons.medication,
          color: Colors.green,
        ),
        _buildStatCard(
          title: 'CME Credits',
          value: '${data['cme_credits'] ?? 0}',
          change: data['cme_change'],
          icon: Icons.school,
          color: Colors.purple,
        ),
        _buildStatCard(
          title: 'Streak',
          value: '${data['streak'] ?? 0} days',
          icon: Icons.local_fire_department,
          color: Colors.orange,
        ),
      ],
    );
  }

  Widget _buildStatCard({
    required String title,
    required String value,
    double? change,
    required IconData icon,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: DoraColors.bgSecondary,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: DoraColors.borderColor),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Icon(icon, color: color, size: 20),
              if (change != null)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: change >= 0 ? Colors.green.withOpacity(0.1) : Colors.red.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    '${change >= 0 ? '+' : ''}${change.toStringAsFixed(0)}%',
                    style: TextStyle(
                      fontSize: 10,
                      color: change >= 0 ? Colors.green : Colors.red,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
            ],
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                value,
                style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              ),
              Text(
                title,
                style: TextStyle(color: DoraColors.textSecondary, fontSize: 12),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildQueryTrends(List trends) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Query Activity',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 16),
        Container(
          height: 120,
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: DoraColors.bgSecondary,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: List.generate(
              trends.length > 7 ? 7 : trends.length,
              (index) {
                final value = (trends[index]['count'] ?? 0) as num;
                final maxValue = trends.map((t) => (t['count'] ?? 0) as num).reduce((a, b) => a > b ? a : b);
                final height = maxValue > 0 ? (value / maxValue * 80) : 0.0;

                return Expanded(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 4),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        Container(
                          height: height.toDouble(),
                          decoration: BoxDecoration(
                            color: DoraColors.primary,
                            borderRadius: BorderRadius.circular(4),
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          trends[index]['label'] ?? '',
                          style: TextStyle(
                            fontSize: 10,
                            color: DoraColors.textSecondary,
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildTopTopics(List topics) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Top Query Topics',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 16),
        ...topics.take(5).map((topic) {
          final percentage = (topic['percentage'] ?? 0.0) as double;
          return Container(
            margin: const EdgeInsets.only(bottom: 12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(topic['name'] ?? '', style: const TextStyle(fontWeight: FontWeight.w500)),
                    Text('${topic['count'] ?? 0}', style: TextStyle(color: DoraColors.textSecondary)),
                  ],
                ),
                const SizedBox(height: 4),
                LinearProgressIndicator(
                  value: percentage / 100,
                  backgroundColor: DoraColors.borderColor,
                  valueColor: AlwaysStoppedAnimation<Color>(DoraColors.primary),
                  borderRadius: BorderRadius.circular(2),
                ),
              ],
            ),
          );
        }),
      ],
    );
  }

  Widget _buildPrescriptionStats(Map<String, dynamic> prescriptions) {
    final topDrugs = prescriptions['top_drugs'] as List? ?? [];
    final genericRate = prescriptions['generic_rate'] ?? 0.0;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Prescription Patterns',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 16),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: DoraColors.bgSecondary,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Column(
            children: [
              Row(
                children: [
                  Expanded(
                    child: Column(
                      children: [
                        Text(
                          '${(genericRate * 100).toStringAsFixed(0)}%',
                          style: TextStyle(
                            fontSize: 32,
                            fontWeight: FontWeight.bold,
                            color: DoraColors.success,
                          ),
                        ),
                        Text(
                          'Generic Prescriptions',
                          style: TextStyle(color: DoraColors.textSecondary, fontSize: 12),
                        ),
                      ],
                    ),
                  ),
                  Container(width: 1, height: 60, color: DoraColors.borderColor),
                  Expanded(
                    child: Column(
                      children: [
                        Text(
                          '${topDrugs.length}',
                          style: const TextStyle(fontSize: 32, fontWeight: FontWeight.bold),
                        ),
                        Text(
                          'Unique Drugs',
                          style: TextStyle(color: DoraColors.textSecondary, fontSize: 12),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              if (topDrugs.isNotEmpty) ...[
                const SizedBox(height: 16),
                const Divider(),
                const SizedBox(height: 8),
                ...topDrugs.take(3).map((drug) => Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(drug['name'] ?? ''),
                      Text('${drug['count'] ?? 0}', style: TextStyle(color: DoraColors.textSecondary)),
                    ],
                  ),
                )),
              ],
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildLearningProgress(Map<String, dynamic> learning) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Learning Progress',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 16),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: DoraColors.bgSecondary,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Column(
            children: [
              Row(
                children: [
                  _buildLearningMetric(
                    icon: Icons.quiz,
                    value: '${learning['quizzes_completed'] ?? 0}',
                    label: 'Quizzes',
                    color: Colors.blue,
                  ),
                  _buildLearningMetric(
                    icon: Icons.school,
                    value: '${learning['cme_credits'] ?? 0}',
                    label: 'CME Credits',
                    color: Colors.purple,
                  ),
                  _buildLearningMetric(
                    icon: Icons.lightbulb,
                    value: '${learning['pearls_read'] ?? 0}',
                    label: 'Pearls',
                    color: Colors.amber,
                  ),
                ],
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildLearningMetric({
    required IconData icon,
    required String value,
    required String label,
    required Color color,
  }) {
    return Expanded(
      child: Column(
        children: [
          Icon(icon, color: color, size: 28),
          const SizedBox(height: 8),
          Text(
            value,
            style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          ),
          Text(
            label,
            style: TextStyle(color: DoraColors.textSecondary, fontSize: 11),
          ),
        ],
      ),
    );
  }
}
