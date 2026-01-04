import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../theme.dart';
import '../services/api_client.dart';

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  final _licenseController = TextEditingController();
  bool _isActivating = false;

  @override
  void dispose() {
    _licenseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final connectionStatus = ref.watch(connectionStatusProvider);

    return Scaffold(
      backgroundColor: DoraColors.bgSecondary,
      appBar: AppBar(
        title: const Text('Settings'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Connection status
          _buildSection(
            title: 'CONNECTION',
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: DoraColors.bgPrimary,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  connectionStatus.when(
                    data: (connected) => Container(
                      width: 12,
                      height: 12,
                      decoration: BoxDecoration(
                        color: connected ? DoraColors.success : DoraColors.error,
                        shape: BoxShape.circle,
                      ),
                    ),
                    loading: () => const SizedBox(
                      width: 12,
                      height: 12,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                    error: (_, __) => Container(
                      width: 12,
                      height: 12,
                      decoration: const BoxDecoration(
                        color: DoraColors.error,
                        shape: BoxShape.circle,
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'API Connection',
                          style: TextStyle(
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                        connectionStatus.when(
                          data: (connected) => Text(
                            connected ? 'Connected' : 'Disconnected',
                            style: TextStyle(
                              fontSize: 13,
                              color: connected
                                  ? DoraColors.success
                                  : DoraColors.error,
                            ),
                          ),
                          loading: () => const Text(
                            'Checking...',
                            style: TextStyle(
                              fontSize: 13,
                              color: DoraColors.textSecondary,
                            ),
                          ),
                          error: (_, __) => const Text(
                            'Error',
                            style: TextStyle(
                              fontSize: 13,
                              color: DoraColors.error,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.refresh),
                    onPressed: () => ref.refresh(connectionStatusProvider),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),

          // License
          _buildSection(
            title: 'LICENSE',
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: DoraColors.bgPrimary,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.verified_user, color: DoraColors.warning),
                      const SizedBox(width: 12),
                      const Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Free Tier',
                              style: TextStyle(
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            Text(
                              '10 queries per day',
                              style: TextStyle(
                                fontSize: 13,
                                color: DoraColors.textSecondary,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _licenseController,
                    decoration: const InputDecoration(
                      labelText: 'License Key',
                      hintText: 'Enter your license key',
                    ),
                    obscureText: true,
                  ),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: _isActivating ? null : _activateLicense,
                      child: _isActivating
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                valueColor:
                                    AlwaysStoppedAnimation(Colors.white),
                              ),
                            )
                          : const Text('Activate'),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),

          // About
          _buildSection(
            title: 'ABOUT',
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: DoraColors.bgPrimary,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                children: [
                  _buildInfoRow('Version', '1.0.0'),
                  const Divider(height: 24),
                  _buildInfoRow('Build', '2026.01'),
                  const Divider(height: 24),
                  const Row(
                    children: [
                      Expanded(
                        child: Text(
                          '© 2026 DocAssist',
                          style: TextStyle(
                            color: DoraColors.textSecondary,
                            fontSize: 13,
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),

          // Links
          _buildSection(
            title: 'SUPPORT',
            child: Container(
              decoration: BoxDecoration(
                color: DoraColors.bgPrimary,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                children: [
                  _buildLinkTile(
                    icon: Icons.description_outlined,
                    title: 'Documentation',
                    onTap: () {},
                  ),
                  const Divider(height: 1),
                  _buildLinkTile(
                    icon: Icons.privacy_tip_outlined,
                    title: 'Privacy Policy',
                    onTap: () {},
                  ),
                  const Divider(height: 1),
                  _buildLinkTile(
                    icon: Icons.article_outlined,
                    title: 'Terms of Service',
                    onTap: () {},
                  ),
                  const Divider(height: 1),
                  _buildLinkTile(
                    icon: Icons.help_outline,
                    title: 'Help & Support',
                    onTap: () {},
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSection({required String title, required Widget child}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(left: 4, bottom: 8),
          child: Text(
            title,
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: DoraColors.textTertiary,
              letterSpacing: 0.5,
            ),
          ),
        ),
        child,
      ],
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: const TextStyle(color: DoraColors.textSecondary),
        ),
        Text(
          value,
          style: const TextStyle(fontWeight: FontWeight.w500),
        ),
      ],
    );
  }

  Widget _buildLinkTile({
    required IconData icon,
    required String title,
    required VoidCallback onTap,
  }) {
    return ListTile(
      leading: Icon(icon, color: DoraColors.textSecondary),
      title: Text(title),
      trailing: const Icon(
        Icons.chevron_right,
        color: DoraColors.textTertiary,
      ),
      onTap: onTap,
    );
  }

  Future<void> _activateLicense() async {
    final key = _licenseController.text.trim();
    if (key.isEmpty) return;

    setState(() => _isActivating = true);

    final client = ref.read(apiClientProvider);
    final result = await client.activateLicense(key);

    setState(() => _isActivating = false);

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            result['success'] == true
                ? 'License activated successfully!'
                : result['error'] ?? 'Failed to activate license',
          ),
          backgroundColor:
              result['success'] == true ? DoraColors.success : DoraColors.error,
        ),
      );
    }
  }
}
