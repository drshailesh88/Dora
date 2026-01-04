/// Subscription Management Screen
///
/// View and manage current subscription, upgrade/downgrade plans.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../theme.dart';
import '../../providers/billing_provider.dart';
import 'pricing_plans_screen.dart';
import 'payment_history_screen.dart';

class SubscriptionScreen extends ConsumerWidget {
  const SubscriptionScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final subscription = ref.watch(currentSubscriptionProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Subscription'),
        backgroundColor: DoraColors.bgPrimary,
        elevation: 0,
      ),
      body: subscription.when(
        data: (data) => _buildSubscriptionView(context, ref, data),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => _buildNoSubscription(context),
      ),
    );
  }

  Widget _buildSubscriptionView(
    BuildContext context,
    WidgetRef ref,
    Map<String, dynamic>? subscription,
  ) {
    if (subscription == null) {
      return _buildNoSubscription(context);
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildCurrentPlanCard(context, subscription),
          const SizedBox(height: 24),
          _buildUsageSection(subscription),
          const SizedBox(height: 24),
          _buildBillingInfoSection(subscription),
          const SizedBox(height: 24),
          _buildActionsSection(context, ref, subscription),
          const SizedBox(height: 24),
          _buildQuickLinks(context),
        ],
      ),
    );
  }

  Widget _buildCurrentPlanCard(
    BuildContext context,
    Map<String, dynamic> subscription,
  ) {
    final plan = subscription['plan'] ?? {};
    final status = subscription['status'] ?? 'active';
    final isTrial = subscription['is_trial'] ?? false;

    Color statusColor;
    String statusLabel;
    switch (status) {
      case 'active':
        statusColor = Colors.green;
        statusLabel = isTrial ? 'Trial Active' : 'Active';
        break;
      case 'past_due':
        statusColor = Colors.orange;
        statusLabel = 'Payment Due';
        break;
      case 'cancelled':
        statusColor = Colors.red;
        statusLabel = 'Cancelled';
        break;
      default:
        statusColor = Colors.grey;
        statusLabel = status.toString().toUpperCase();
    }

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [DoraColors.primary, DoraColors.primary.withOpacity(0.7)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                plan['name'] ?? 'Professional',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                decoration: BoxDecoration(
                  color: statusColor.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: statusColor),
                ),
                child: Text(
                  statusLabel,
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            plan['description'] ?? 'Full access to all features',
            style: TextStyle(
              color: Colors.white.withOpacity(0.9),
              fontSize: 14,
            ),
          ),
          const SizedBox(height: 20),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _formatPrice(subscription['amount'] ?? 99900),
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Text(
                    '/${subscription['billing_cycle'] ?? 'month'}',
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.7),
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
              if (isTrial)
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Column(
                    children: [
                      Text(
                        '${subscription['trial_days_left'] ?? 7}',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Text(
                        'days left',
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.7),
                          fontSize: 10,
                        ),
                      ),
                    ],
                  ),
                ),
            ],
          ),
          if (subscription['next_billing_date'] != null) ...[
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  const Icon(Icons.calendar_today, color: Colors.white, size: 16),
                  const SizedBox(width: 8),
                  Text(
                    'Next billing: ${_formatDate(subscription['next_billing_date'])}',
                    style: const TextStyle(color: Colors.white, fontSize: 14),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildUsageSection(Map<String, dynamic> subscription) {
    final usage = subscription['usage'] ?? {};
    final limits = subscription['limits'] ?? {};

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Usage This Month',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 16),
        _buildUsageItem(
          icon: Icons.search,
          label: 'Queries',
          used: usage['queries'] ?? 0,
          limit: limits['queries'] ?? -1,
        ),
        const SizedBox(height: 12),
        _buildUsageItem(
          icon: Icons.cloud_upload,
          label: 'Document Uploads',
          used: usage['documents'] ?? 0,
          limit: limits['documents'] ?? -1,
        ),
        const SizedBox(height: 12),
        _buildUsageItem(
          icon: Icons.storage,
          label: 'Storage',
          used: usage['storage_mb'] ?? 0,
          limit: limits['storage_mb'] ?? -1,
          isMB: true,
        ),
      ],
    );
  }

  Widget _buildUsageItem({
    required IconData icon,
    required String label,
    required int used,
    required int limit,
    bool isMB = false,
  }) {
    final isUnlimited = limit < 0;
    final percentage = isUnlimited ? 0.0 : (used / limit).clamp(0.0, 1.0);
    final isNearLimit = percentage > 0.8;

    String usedText = isMB ? '${(used / 1024).toStringAsFixed(1)} GB' : '$used';
    String limitText = isUnlimited
        ? 'Unlimited'
        : isMB
            ? '${(limit / 1024).toStringAsFixed(1)} GB'
            : '$limit';

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: DoraColors.bgSecondary,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Icon(icon, color: DoraColors.primary, size: 20),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  label,
                  style: const TextStyle(fontWeight: FontWeight.w500),
                ),
              ),
              Text(
                '$usedText / $limitText',
                style: TextStyle(
                  color: isNearLimit ? Colors.orange : DoraColors.textSecondary,
                  fontWeight: isNearLimit ? FontWeight.bold : FontWeight.normal,
                ),
              ),
            ],
          ),
          if (!isUnlimited) ...[
            const SizedBox(height: 8),
            LinearProgressIndicator(
              value: percentage,
              backgroundColor: DoraColors.borderColor,
              valueColor: AlwaysStoppedAnimation(
                isNearLimit ? Colors.orange : DoraColors.primary,
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildBillingInfoSection(Map<String, dynamic> subscription) {
    final billingInfo = subscription['billing_info'] ?? {};

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Billing Information',
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
              _buildInfoRow(
                'Payment Method',
                billingInfo['payment_method'] ?? 'Card ending in 4242',
                Icons.credit_card,
              ),
              const Divider(height: 24),
              _buildInfoRow(
                'Billing Email',
                billingInfo['email'] ?? 'doctor@clinic.com',
                Icons.email,
              ),
              const Divider(height: 24),
              _buildInfoRow(
                'GSTIN',
                billingInfo['gstin'] ?? 'Not provided',
                Icons.business,
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildInfoRow(String label, String value, IconData icon) {
    return Row(
      children: [
        Icon(icon, color: DoraColors.textSecondary, size: 20),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: TextStyle(
                  color: DoraColors.textSecondary,
                  fontSize: 12,
                ),
              ),
              Text(value, style: const TextStyle(fontWeight: FontWeight.w500)),
            ],
          ),
        ),
        const Icon(Icons.edit, size: 16, color: Colors.grey),
      ],
    );
  }

  Widget _buildActionsSection(
    BuildContext context,
    WidgetRef ref,
    Map<String, dynamic> subscription,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Manage Subscription',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 16),
        Row(
          children: [
            Expanded(
              child: ElevatedButton.icon(
                onPressed: () => Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => const PricingPlansScreen(isUpgrade: true),
                  ),
                ),
                icon: const Icon(Icons.upgrade),
                label: const Text('Upgrade'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: OutlinedButton.icon(
                onPressed: () => _showCancelDialog(context, ref),
                icon: const Icon(Icons.cancel),
                label: const Text('Cancel'),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  foregroundColor: Colors.red,
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildQuickLinks(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Quick Links',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 12),
        ListTile(
          leading: Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: DoraColors.primary.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(Icons.receipt_long, color: DoraColors.primary),
          ),
          title: const Text('Payment History'),
          subtitle: const Text('View past payments and invoices'),
          trailing: const Icon(Icons.chevron_right),
          onTap: () => Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const PaymentHistoryScreen()),
          ),
        ),
        ListTile(
          leading: Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.orange.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(Icons.compare_arrows, color: Colors.orange),
          ),
          title: const Text('Compare Plans'),
          subtitle: const Text('See all plan features'),
          trailing: const Icon(Icons.chevron_right),
          onTap: () => Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const PricingPlansScreen()),
          ),
        ),
        ListTile(
          leading: Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.green.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(Icons.support_agent, color: Colors.green),
          ),
          title: const Text('Billing Support'),
          subtitle: const Text('Get help with billing'),
          trailing: const Icon(Icons.chevron_right),
          onTap: () {},
        ),
      ],
    );
  }

  Widget _buildNoSubscription(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.card_membership,
              size: 80,
              color: DoraColors.textSecondary.withOpacity(0.5),
            ),
            const SizedBox(height: 24),
            const Text(
              'No Active Subscription',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            Text(
              'Subscribe to unlock all features and get unlimited access to medical knowledge.',
              textAlign: TextAlign.center,
              style: TextStyle(color: DoraColors.textSecondary, fontSize: 16),
            ),
            const SizedBox(height: 32),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () => Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const PricingPlansScreen()),
                ),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: const Text('View Plans', style: TextStyle(fontSize: 16)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showCancelDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Cancel Subscription?'),
        content: const Text(
          'Your subscription will remain active until the end of the current billing period. '
          'You can resubscribe anytime.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Keep Subscription'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              ref.read(subscriptionActionsProvider.notifier).cancel();
            },
            child: const Text(
              'Cancel Subscription',
              style: TextStyle(color: Colors.red),
            ),
          ),
        ],
      ),
    );
  }

  String _formatPrice(int paise) {
    final rupees = paise / 100;
    return '₹${rupees.toStringAsFixed(0)}';
  }

  String _formatDate(String? isoDate) {
    if (isoDate == null) return 'N/A';
    try {
      final date = DateTime.parse(isoDate);
      return '${date.day}/${date.month}/${date.year}';
    } catch (e) {
      return isoDate;
    }
  }
}
