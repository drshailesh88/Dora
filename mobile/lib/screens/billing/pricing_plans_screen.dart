/// Pricing Plans Screen
///
/// Display and compare subscription plans.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../theme.dart';
import '../../providers/billing_provider.dart';

class PricingPlansScreen extends ConsumerStatefulWidget {
  final bool isUpgrade;

  const PricingPlansScreen({super.key, this.isUpgrade = false});

  @override
  ConsumerState<PricingPlansScreen> createState() => _PricingPlansScreenState();
}

class _PricingPlansScreenState extends ConsumerState<PricingPlansScreen> {
  String _billingCycle = 'yearly'; // monthly, quarterly, yearly

  @override
  Widget build(BuildContext context) {
    final plans = ref.watch(availablePlansProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(widget.isUpgrade ? 'Upgrade Plan' : 'Choose a Plan'),
        backgroundColor: DoraColors.bgPrimary,
        elevation: 0,
      ),
      body: plans.when(
        data: (data) => _buildPlansView(data),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error loading plans: $e')),
      ),
    );
  }

  Widget _buildPlansView(List<Map<String, dynamic>> plans) {
    return Column(
      children: [
        _buildBillingToggle(),
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: plans.length,
            itemBuilder: (context, index) => _buildPlanCard(plans[index]),
          ),
        ),
      ],
    );
  }

  Widget _buildBillingToggle() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _buildCycleOption('monthly', 'Monthly'),
              const SizedBox(width: 8),
              _buildCycleOption('quarterly', 'Quarterly'),
              const SizedBox(width: 8),
              _buildCycleOption('yearly', 'Yearly'),
            ],
          ),
          if (_billingCycle == 'yearly')
            Container(
              margin: const EdgeInsets.only(top: 8),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.green.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Text(
                '🎉 Save 20% with yearly billing!',
                style: TextStyle(color: Colors.green, fontSize: 12),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildCycleOption(String value, String label) {
    final isSelected = _billingCycle == value;

    return GestureDetector(
      onTap: () => setState(() => _billingCycle = value),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? DoraColors.primary : DoraColors.bgSecondary,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isSelected ? Colors.white : DoraColors.textSecondary,
            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
          ),
        ),
      ),
    );
  }

  Widget _buildPlanCard(Map<String, dynamic> plan) {
    final isRecommended = plan['is_recommended'] ?? false;
    final isCurrentPlan = plan['is_current'] ?? false;
    final priceKey = 'price_$_billingCycle';
    final price = plan[priceKey] ?? plan['price_monthly'] ?? 0;

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        border: Border.all(
          color: isRecommended ? DoraColors.primary : DoraColors.borderColor,
          width: isRecommended ? 2 : 1,
        ),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        children: [
          if (isRecommended)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 8),
              decoration: BoxDecoration(
                color: DoraColors.primary,
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(14),
                  topRight: Radius.circular(14),
                ),
              ),
              child: const Text(
                '⭐ RECOMMENDED',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 12,
                ),
              ),
            ),
          Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      plan['name'] ?? 'Plan',
                      style: const TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    if (isCurrentPlan)
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.green.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Text(
                          'Current',
                          style: TextStyle(
                            color: Colors.green,
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  plan['description'] ?? '',
                  style: TextStyle(
                    color: DoraColors.textSecondary,
                    fontSize: 14,
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      _formatPrice(price),
                      style: const TextStyle(
                        fontSize: 32,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(width: 4),
                    Text(
                      '/$_billingCycle',
                      style: TextStyle(
                        color: DoraColors.textSecondary,
                        fontSize: 14,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                const Divider(),
                const SizedBox(height: 12),
                ...((plan['features'] ?? []) as List)
                    .map((f) => _buildFeatureItem(f.toString()))
                    .toList(),
                const SizedBox(height: 20),
                SizedBox(
                  width: double.infinity,
                  child: isCurrentPlan
                      ? OutlinedButton(
                          onPressed: null,
                          style: OutlinedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 14),
                          ),
                          child: const Text('Current Plan'),
                        )
                      : ElevatedButton(
                          onPressed: () => _selectPlan(plan),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: isRecommended
                                ? DoraColors.primary
                                : DoraColors.bgSecondary,
                            foregroundColor: isRecommended
                                ? Colors.white
                                : DoraColors.textPrimary,
                            padding: const EdgeInsets.symmetric(vertical: 14),
                          ),
                          child: Text(
                            widget.isUpgrade
                                ? 'Upgrade to ${plan['name']}'
                                : 'Select ${plan['name']}',
                          ),
                        ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFeatureItem(String feature) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          Icon(Icons.check_circle, color: Colors.green, size: 18),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              feature,
              style: const TextStyle(fontSize: 14),
            ),
          ),
        ],
      ),
    );
  }

  void _selectPlan(Map<String, dynamic> plan) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => _buildCheckoutSheet(plan),
    );
  }

  Widget _buildCheckoutSheet(Map<String, dynamic> plan) {
    final priceKey = 'price_$_billingCycle';
    final price = plan[priceKey] ?? plan['price_monthly'] ?? 0;

    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: Colors.grey[300],
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(height: 24),
          const Text(
            'Confirm Subscription',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 24),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: DoraColors.bgSecondary,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Column(
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('Plan'),
                    Text(
                      plan['name'] ?? 'Professional',
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('Billing Cycle'),
                    Text(
                      _billingCycle.toUpperCase(),
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
                const Divider(height: 24),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('Subtotal'),
                    Text(_formatPrice(price)),
                  ],
                ),
                const SizedBox(height: 8),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('GST (18%)'),
                    Text(_formatPrice((price * 0.18).round())),
                  ],
                ),
                const Divider(height: 24),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      'Total',
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                    Text(
                      _formatPrice((price * 1.18).round()),
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 20,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () => _processPayment(plan),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
              child: const Text(
                'Proceed to Payment',
                style: TextStyle(fontSize: 16),
              ),
            ),
          ),
          const SizedBox(height: 12),
          Text(
            'Secure payment powered by Razorpay',
            style: TextStyle(color: DoraColors.textSecondary, fontSize: 12),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  void _processPayment(Map<String, dynamic> plan) {
    Navigator.pop(context); // Close bottom sheet

    // In production, integrate with Razorpay SDK
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Payment Processing'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const CircularProgressIndicator(),
            const SizedBox(height: 16),
            Text('Redirecting to payment gateway...'),
          ],
        ),
      ),
    );

    // Simulate payment
    Future.delayed(const Duration(seconds: 2), () {
      Navigator.pop(context); // Close dialog
      _showSuccessDialog();
    });
  }

  void _showSuccessDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            Icon(Icons.check_circle, color: Colors.green, size: 32),
            const SizedBox(width: 12),
            const Text('Success!'),
          ],
        ),
        content: const Text(
          'Your subscription has been activated. Welcome to DocAssist Dora!',
        ),
        actions: [
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              Navigator.pop(context);
            },
            child: const Text('Get Started'),
          ),
        ],
      ),
    );
  }

  String _formatPrice(int paise) {
    final rupees = paise / 100;
    return '₹${rupees.toStringAsFixed(0)}';
  }
}
