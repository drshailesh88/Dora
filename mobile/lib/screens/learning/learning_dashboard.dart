import 'package:flutter/material.dart';
import '../../widgets/learning/streak_widget.dart';
import '../../widgets/learning/progress_ring.dart';

/// Learning Dashboard Screen
///
/// Main dashboard for CME learning with streaks, credits, and achievements
class LearningDashboard extends StatefulWidget {
  const LearningDashboard({Key? key}) : super(key: key);

  @override
  _LearningDashboardState createState() => _LearningDashboardState();
}

class _LearningDashboardState extends State<LearningDashboard> {
  bool _isLoading = true;
  Map<String, dynamic>? _dashboardData;

  @override
  void initState() {
    super.initState();
    _loadDashboard();
  }

  Future<void> _loadDashboard() async {
    // TODO: Replace with actual API call
    // final response = await http.get(Uri.parse('$apiBaseUrl/api/learning/dashboard'));
    // final data = jsonDecode(response.body);

    // Mock data for demonstration
    await Future.delayed(const Duration(seconds: 1));

    setState(() {
      _dashboardData = {
        'streak': {
          'current_streak': 15,
          'longest_streak': 30,
          'status': 'active',
          'next_milestone': 30,
          'freeze_tokens': 2,
        },
        'cme_credits': {
          'total_credits': 18.5,
          'annual_requirement': 30.0,
          'progress_percentage': 61.7,
          'credits_remaining': 11.5,
        },
        'achievements': {
          'earned': 12,
          'level': {
            'current_level': 5,
            'total_points': 1250,
            'progress_percentage': 65.0,
            'points_needed_for_next': 350,
          },
        },
        'quiz_performance': {
          'total_attempts': 25,
          'quizzes_passed': 20,
          'average_score': 0.82,
        },
      };
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Learning Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications_outlined),
            onPressed: () {
              // Navigate to notifications
            },
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadDashboard,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  // Streak Card
                  _buildStreakCard(),
                  const SizedBox(height: 16),

                  // Stats Grid
                  _buildStatsGrid(),
                  const SizedBox(height: 16),

                  // Quick Actions
                  _buildQuickActions(),
                  const SizedBox(height: 16),

                  // Recent Activity
                  _buildRecentActivity(),
                ],
              ),
            ),
    );
  }

  Widget _buildStreakCard() {
    final streak = _dashboardData!['streak'];

    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          gradient: LinearGradient(
            colors: [Colors.orange.shade400, Colors.deepOrange.shade600],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    '🔥 Learning Streak',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      '${streak['freeze_tokens']} freeze',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Text(
                '${streak['current_streak']} Days',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 36,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Longest streak: ${streak['longest_streak']} days',
                style: TextStyle(
                  color: Colors.white.withOpacity(0.9),
                  fontSize: 14,
                ),
              ),
              const SizedBox(height: 12),
              LinearProgressIndicator(
                value: streak['current_streak'] / streak['next_milestone'],
                backgroundColor: Colors.white.withOpacity(0.3),
                valueColor: const AlwaysStoppedAnimation<Color>(Colors.white),
              ),
              const SizedBox(height: 8),
              Text(
                '${streak['next_milestone'] - streak['current_streak']} days to ${streak['next_milestone']}-day milestone',
                style: TextStyle(
                  color: Colors.white.withOpacity(0.9),
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatsGrid() {
    final cmeCredits = _dashboardData!['cme_credits'];
    final achievements = _dashboardData!['achievements'];
    final quizPerf = _dashboardData!['quiz_performance'];

    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: 12,
      crossAxisSpacing: 12,
      childAspectRatio: 1.1,
      children: [
        _buildStatCard(
          title: 'CME Credits',
          value: cmeCredits['total_credits'].toStringAsFixed(1),
          subtitle: 'of ${cmeCredits['annual_requirement']} required',
          icon: Icons.emoji_events_outlined,
          color: Colors.blue,
          progress: cmeCredits['progress_percentage'] / 100,
        ),
        _buildStatCard(
          title: 'Achievements',
          value: '${achievements['earned']}',
          subtitle: 'Level ${achievements['level']['current_level']}',
          icon: Icons.stars_outlined,
          color: Colors.purple,
          progress: achievements['level']['progress_percentage'] / 100,
        ),
        _buildStatCard(
          title: 'Quiz Score',
          value: '${(quizPerf['average_score'] * 100).toStringAsFixed(0)}%',
          subtitle: '${quizPerf['quizzes_passed']} passed',
          icon: Icons.quiz_outlined,
          color: Colors.green,
          progress: quizPerf['average_score'],
        ),
        _buildStatCard(
          title: 'Attempts',
          value: '${quizPerf['total_attempts']}',
          subtitle: 'Total quizzes',
          icon: Icons.assessment_outlined,
          color: Colors.orange,
          progress: null,
        ),
      ],
    );
  }

  Widget _buildStatCard({
    required String title,
    required String value,
    required String subtitle,
    required IconData icon,
    required Color color,
    double? progress,
  }) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    color: Colors.grey.shade600,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                Icon(icon, color: color, size: 20),
              ],
            ),
            const Spacer(),
            Text(
              value,
              style: const TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              subtitle,
              style: TextStyle(
                color: Colors.grey.shade600,
                fontSize: 11,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            if (progress != null) ...[
              const SizedBox(height: 8),
              LinearProgressIndicator(
                value: progress,
                backgroundColor: color.withOpacity(0.2),
                valueColor: AlwaysStoppedAnimation<Color>(color),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildQuickActions() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Quick Actions',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: _buildActionButton(
                label: 'Take Quiz',
                icon: Icons.quiz,
                color: Colors.blue,
                onTap: () {
                  Navigator.pushNamed(context, '/learning/quiz');
                },
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildActionButton(
                label: 'Learning Paths',
                icon: Icons.route,
                color: Colors.green,
                onTap: () {
                  Navigator.pushNamed(context, '/learning/paths');
                },
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildActionButton({
    required String label,
    required IconData icon,
    required Color color,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 20),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withOpacity(0.3)),
        ),
        child: Column(
          children: [
            Icon(icon, color: color, size: 32),
            const SizedBox(height: 8),
            Text(
              label,
              style: TextStyle(
                color: color,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRecentActivity() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Recent Activity',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 12),
        Card(
          child: ListTile(
            leading: const CircleAvatar(
              backgroundColor: Colors.blue,
              child: Icon(Icons.quiz, color: Colors.white, size: 20),
            ),
            title: const Text('Quiz: Cardiology Basics'),
            subtitle: const Text('Passed • 85% score • 0.5 credits'),
            trailing: const Text('2h ago', style: TextStyle(fontSize: 12)),
          ),
        ),
        Card(
          child: ListTile(
            leading: const CircleAvatar(
              backgroundColor: Colors.green,
              child: Icon(Icons.check_circle, color: Colors.white, size: 20),
            ),
            title: const Text('Module Completed'),
            subtitle: const Text('Emergency Medicine • 2.0 credits'),
            trailing: const Text('1d ago', style: TextStyle(fontSize: 12)),
          ),
        ),
      ],
    );
  }
}
