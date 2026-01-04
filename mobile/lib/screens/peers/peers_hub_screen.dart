import 'package:flutter/material.dart';

/// Peer Network Hub Screen
///
/// Main landing page for the specialist peer network.
/// Doctors can connect with specialist peers for consultations and case discussions.
class PeersHubScreen extends StatelessWidget {
  const PeersHubScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Peer Network'),
        backgroundColor: Colors.blue,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            const Text(
              'Connect with Specialist Peers',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Get expert consultations and discuss interesting cases',
              style: TextStyle(color: Colors.grey),
            ),
            const SizedBox(height: 24),

            // Quick Actions Grid
            GridView.count(
              crossAxisCount: 2,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              mainAxisSpacing: 16,
              crossAxisSpacing: 16,
              children: [
                _buildActionCard(
                  context,
                  icon: Icons.chat,
                  title: 'Ask a Specialist',
                  subtitle: 'Get expert consultation',
                  color: Colors.blue,
                  onTap: () {
                    Navigator.pushNamed(context, '/peers/consult');
                  },
                ),
                _buildActionCard(
                  context,
                  icon: Icons.people,
                  title: 'Find Specialists',
                  subtitle: 'Browse directory',
                  color: Colors.green,
                  onTap: () {
                    Navigator.pushNamed(context, '/peers/specialists');
                  },
                ),
                _buildActionCard(
                  context,
                  icon: Icons.book,
                  title: 'Case Library',
                  subtitle: 'Browse cases',
                  color: Colors.purple,
                  onTap: () {
                    Navigator.pushNamed(context, '/peers/cases');
                  },
                ),
                _buildActionCard(
                  context,
                  icon: Icons.star,
                  title: 'My Profile',
                  subtitle: 'Manage consultations',
                  color: Colors.orange,
                  onTap: () {
                    Navigator.pushNamed(context, '/peers/profile');
                  },
                ),
              ],
            ),
            const SizedBox(height: 24),

            // Stats
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Network Stats',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        _buildStat('1,234', 'Specialists'),
                        _buildStat('5,678', 'Consultations'),
                        _buildStat('892', 'Cases'),
                        _buildStat('4.8', 'Avg. Rating'),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // How It Works
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'How It Works',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 16),
                    _buildStep(
                      '1',
                      'Submit Your Case',
                      'Describe your case with anonymized patient details',
                    ),
                    const SizedBox(height: 12),
                    _buildStep(
                      '2',
                      'Get Matched',
                      'We match you with the best specialist for your case',
                    ),
                    const SizedBox(height: 12),
                    _buildStep(
                      '3',
                      'Receive Expert Opinion',
                      'Get detailed recommendations from verified specialists',
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActionCard(
    BuildContext context, {
    required IconData icon,
    required String title,
    required String subtitle,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Card(
      elevation: 2,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 48, color: color),
              const SizedBox(height: 12),
              Text(
                title,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                subtitle,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 12,
                  color: Colors.grey,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStat(String value, String label) {
    return Column(
      children: [
        Text(
          value,
          style: const TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: Colors.blue,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: const TextStyle(
            fontSize: 12,
            color: Colors.grey,
          ),
        ),
      ],
    );
  }

  Widget _buildStep(String number, String title, String description) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 32,
          height: 32,
          decoration: BoxDecoration(
            color: Colors.blue.shade100,
            shape: BoxShape.circle,
          ),
          child: Center(
            child: Text(
              number,
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                color: Colors.blue,
              ),
            ),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                description,
                style: const TextStyle(
                  fontSize: 14,
                  color: Colors.grey,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
