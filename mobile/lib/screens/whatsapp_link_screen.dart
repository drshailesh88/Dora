import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/whatsapp_service.dart';

/// WhatsApp Account Linking Screen
///
/// Allows users to:
/// - Link their WhatsApp account via 6-digit code
/// - View QR code for quick linking
/// - Manage WhatsApp preferences
/// - Unlink account
class WhatsAppLinkScreen extends StatefulWidget {
  const WhatsAppLinkScreen({Key? key}) : super(key: key);

  @override
  State<WhatsAppLinkScreen> createState() => _WhatsAppLinkScreenState();
}

class _WhatsAppLinkScreenState extends State<WhatsAppLinkScreen> {
  final WhatsAppService _whatsappService = WhatsAppService();
  final TextEditingController _codeController = TextEditingController();

  bool _isLinked = false;
  String? _whatsappId;
  bool _isLoading = true;
  bool _isLinking = false;
  bool _showQR = false;

  // Preferences
  bool _voiceResponses = true;
  bool _notificationsEnabled = true;
  String _preferredFormat = 'concise';

  @override
  void initState() {
    super.initState();
    _loadLinkStatus();
  }

  @override
  void dispose() {
    _codeController.dispose();
    super.dispose();
  }

  Future<void> _loadLinkStatus() async {
    setState(() => _isLoading = true);

    try {
      final status = await _whatsappService.getLinkStatus();

      setState(() {
        _isLinked = status['linked'] ?? false;
        _whatsappId = status['whatsapp_id'];
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      _showError('Failed to load WhatsApp status');
    }
  }

  Future<void> _linkAccount() async {
    final code = _codeController.text.trim();

    if (code.length != 6) {
      _showError('Please enter a valid 6-digit code');
      return;
    }

    setState(() => _isLinking = true);

    try {
      final result = await _whatsappService.linkAccount(code);

      if (result['success'] == true) {
        _showSuccess('WhatsApp account linked successfully!');
        _codeController.clear();
        await _loadLinkStatus();
      } else {
        _showError(result['message'] ?? 'Failed to link account');
      }
    } catch (e) {
      _showError('An error occurred. Please try again.');
    } finally {
      setState(() => _isLinking = false);
    }
  }

  Future<void> _unlinkAccount() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Unlink WhatsApp'),
        content: const Text(
          'Are you sure you want to unlink your WhatsApp account?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Unlink'),
          ),
        ],
      ),
    );

    if (confirm != true) return;

    try {
      await _whatsappService.unlinkAccount();
      _showSuccess('WhatsApp account unlinked');
      await _loadLinkStatus();
    } catch (e) {
      _showError('Failed to unlink account');
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
      ),
    );
  }

  void _showSuccess(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.green,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(title: const Text('WhatsApp')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('WhatsApp Integration'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _buildStatusCard(),
          const SizedBox(height: 16),
          if (!_isLinked) ...[
            _buildLinkCard(),
            const SizedBox(height: 16),
          ],
          _buildFeaturesCard(),
          const SizedBox(height: 16),
          if (_isLinked) _buildPreferencesCard(),
        ],
      ),
    );
  }

  Widget _buildStatusCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.message_outlined,
                  color: _isLinked ? Colors.green : Colors.grey,
                ),
                const SizedBox(width: 8),
                Text(
                  'Connection Status',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const Spacer(),
                Chip(
                  label: Text(_isLinked ? 'Connected' : 'Not Connected'),
                  backgroundColor: _isLinked ? Colors.green.shade100 : Colors.grey.shade200,
                  labelStyle: TextStyle(
                    color: _isLinked ? Colors.green.shade900 : Colors.grey.shade700,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              _isLinked
                  ? 'Your WhatsApp is connected'
                  : 'Link your WhatsApp to use Dora via messaging',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Colors.grey.shade600,
                  ),
            ),
            if (_isLinked && _whatsappId != null) ...[
              const SizedBox(height: 16),
              Text(
                'WhatsApp Number',
                style: Theme.of(context).textTheme.labelMedium,
              ),
              const SizedBox(height: 4),
              Text(_whatsappId!),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: _unlinkAccount,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red,
                  foregroundColor: Colors.white,
                ),
                child: const Text('Unlink WhatsApp'),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildLinkCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Link Your WhatsApp',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.blue.shade50,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'How to Link:',
                    style: Theme.of(context).textTheme.titleSmall,
                  ),
                  const SizedBox(height: 8),
                  const Text('1. Open WhatsApp and message: +1234567890'),
                  const Text('2. Send: link'),
                  const Text('3. You\'ll receive a 6-digit code'),
                  const Text('4. Enter the code below'),
                ],
              ),
            ),
            const SizedBox(height: 16),
            Text(
              '6-Digit Link Code',
              style: Theme.of(context).textTheme.labelLarge,
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _codeController,
                    decoration: const InputDecoration(
                      hintText: '000000',
                      border: OutlineInputBorder(),
                    ),
                    keyboardType: TextInputType.number,
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      fontSize: 24,
                      letterSpacing: 8,
                      fontFamily: 'monospace',
                    ),
                    maxLength: 6,
                    inputFormatters: [
                      FilteringTextInputFormatter.digitsOnly,
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  onPressed: _isLinking ? null : _linkAccount,
                  child: _isLinking
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Link'),
                ),
              ],
            ),
            const SizedBox(height: 16),
            OutlinedButton.icon(
              onPressed: () => setState(() => _showQR = !_showQR),
              icon: Icon(_showQR ? Icons.qr_code : Icons.qr_code_outlined),
              label: Text(_showQR ? 'Hide QR Code' : 'Show QR Code'),
              style: OutlinedButton.styleFrom(
                minimumSize: const Size.fromHeight(48),
              ),
            ),
            if (_showQR) ...[
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: Colors.white,
                  border: Border.all(color: Colors.grey.shade300),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  children: [
                    Container(
                      width: 200,
                      height: 200,
                      color: Colors.grey.shade200,
                      child: const Center(
                        child: Text('QR Code Placeholder'),
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Scan this QR code with your WhatsApp',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Colors.grey.shade600,
                          ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildFeaturesCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'WhatsApp Features',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            Text(
              'What you can do with WhatsApp',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Colors.grey.shade600,
                  ),
            ),
            const SizedBox(height: 16),
            _buildFeatureItem(
              Icons.chat_bubble_outline,
              'Medical Queries',
              'Ask medical questions via text or voice notes',
              Colors.blue,
            ),
            _buildFeatureItem(
              Icons.medication_outlined,
              'Drug Interactions',
              'Quick drug interaction checks',
              Colors.green,
            ),
            _buildFeatureItem(
              Icons.share_outlined,
              'Share with Patients',
              'Send medical information to patients',
              Colors.purple,
            ),
            _buildFeatureItem(
              Icons.notifications_outlined,
              'Notifications',
              'Get important updates and alerts',
              Colors.orange,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFeatureItem(
    IconData icon,
    String title,
    String description,
    Color color,
  ) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: color.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icon, color: color, size: 20),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: Theme.of(context).textTheme.titleSmall,
                ),
                Text(
                  description,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Colors.grey.shade600,
                      ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPreferencesCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Preferences',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            Text(
              'Customize your WhatsApp experience',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Colors.grey.shade600,
                  ),
            ),
            const SizedBox(height: 16),
            SwitchListTile(
              title: const Text('Voice Responses'),
              subtitle: const Text('Receive audio responses to voice notes'),
              value: _voiceResponses,
              onChanged: (value) {
                setState(() => _voiceResponses = value);
                // TODO: Save preference via API
              },
            ),
            SwitchListTile(
              title: const Text('Notifications'),
              subtitle: const Text('Receive important updates via WhatsApp'),
              value: _notificationsEnabled,
              onChanged: (value) {
                setState(() => _notificationsEnabled = value);
                // TODO: Save preference via API
              },
            ),
            const Divider(),
            ListTile(
              title: const Text('Response Format'),
              subtitle: DropdownButton<String>(
                value: _preferredFormat,
                isExpanded: true,
                items: const [
                  DropdownMenuItem(
                    value: 'concise',
                    child: Text('Concise'),
                  ),
                  DropdownMenuItem(
                    value: 'detailed',
                    child: Text('Detailed'),
                  ),
                  DropdownMenuItem(
                    value: 'patient_friendly',
                    child: Text('Patient Friendly'),
                  ),
                ],
                onChanged: (value) {
                  if (value != null) {
                    setState(() => _preferredFormat = value);
                    // TODO: Save preference via API
                  }
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
