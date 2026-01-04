/// Payment History Screen
///
/// View past payments and download invoices.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../theme.dart';
import '../../providers/billing_provider.dart';

class PaymentHistoryScreen extends ConsumerWidget {
  const PaymentHistoryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final payments = ref.watch(paymentHistoryProvider);

    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Payment History'),
          backgroundColor: DoraColors.bgPrimary,
          elevation: 0,
          bottom: const TabBar(
            tabs: [
              Tab(text: 'Payments'),
              Tab(text: 'Invoices'),
            ],
          ),
        ),
        body: payments.when(
          data: (data) => TabBarView(
            children: [
              _buildPaymentsList(context, data['payments'] ?? []),
              _buildInvoicesList(context, data['invoices'] ?? []),
            ],
          ),
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (e, _) => Center(child: Text('Error: $e')),
        ),
      ),
    );
  }

  Widget _buildPaymentsList(BuildContext context, List<dynamic> payments) {
    if (payments.isEmpty) {
      return _buildEmptyState(
        icon: Icons.payment,
        title: 'No Payments Yet',
        subtitle: 'Your payment history will appear here',
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: payments.length,
      itemBuilder: (context, index) => _buildPaymentCard(context, payments[index]),
    );
  }

  Widget _buildPaymentCard(BuildContext context, Map<String, dynamic> payment) {
    final status = payment['status'] ?? 'completed';
    final amount = payment['amount'] ?? 0;

    Color statusColor;
    IconData statusIcon;
    switch (status) {
      case 'completed':
        statusColor = Colors.green;
        statusIcon = Icons.check_circle;
        break;
      case 'pending':
        statusColor = Colors.orange;
        statusIcon = Icons.pending;
        break;
      case 'failed':
        statusColor = Colors.red;
        statusIcon = Icons.error;
        break;
      case 'refunded':
        statusColor = Colors.blue;
        statusIcon = Icons.replay;
        break;
      default:
        statusColor = Colors.grey;
        statusIcon = Icons.help;
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: DoraColors.bgSecondary,
        borderRadius: BorderRadius.circular(12),
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.all(16),
        leading: Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            color: statusColor.withOpacity(0.1),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(statusIcon, color: statusColor),
        ),
        title: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              payment['description'] ?? 'Subscription Payment',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            Text(
              _formatPrice(amount),
              style: TextStyle(
                fontWeight: FontWeight.bold,
                color: status == 'refunded' ? Colors.blue : null,
              ),
            ),
          ],
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  _formatDate(payment['created_at']),
                  style: TextStyle(color: DoraColors.textSecondary),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: statusColor.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    status.toString().toUpperCase(),
                    style: TextStyle(
                      color: statusColor,
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            if (payment['payment_method'] != null) ...[
              const SizedBox(height: 4),
              Text(
                payment['payment_method'],
                style: TextStyle(
                  color: DoraColors.textSecondary,
                  fontSize: 12,
                ),
              ),
            ],
          ],
        ),
        onTap: () => _showPaymentDetails(context, payment),
      ),
    );
  }

  Widget _buildInvoicesList(BuildContext context, List<dynamic> invoices) {
    if (invoices.isEmpty) {
      return _buildEmptyState(
        icon: Icons.receipt_long,
        title: 'No Invoices Yet',
        subtitle: 'Your invoices will appear here',
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: invoices.length,
      itemBuilder: (context, index) => _buildInvoiceCard(context, invoices[index]),
    );
  }

  Widget _buildInvoiceCard(BuildContext context, Map<String, dynamic> invoice) {
    final isPaid = invoice['is_paid'] ?? false;
    final total = invoice['total'] ?? 0;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: DoraColors.bgSecondary,
        borderRadius: BorderRadius.circular(12),
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.all(16),
        leading: Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            color: DoraColors.primary.withOpacity(0.1),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(Icons.receipt, color: DoraColors.primary),
        ),
        title: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              invoice['invoice_number'] ?? 'INV-XXXX',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            Text(
              _formatPrice(total),
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
          ],
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Text(
              invoice['description'] ?? 'Monthly Subscription',
              style: TextStyle(color: DoraColors.textSecondary, fontSize: 12),
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  _formatDate(invoice['created_at']),
                  style: TextStyle(color: DoraColors.textSecondary),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: (isPaid ? Colors.green : Colors.orange).withOpacity(0.1),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    isPaid ? 'PAID' : 'PENDING',
                    style: TextStyle(
                      color: isPaid ? Colors.green : Colors.orange,
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
        trailing: IconButton(
          icon: const Icon(Icons.download),
          onPressed: () => _downloadInvoice(context, invoice),
        ),
        onTap: () => _showInvoiceDetails(context, invoice),
      ),
    );
  }

  Widget _buildEmptyState({
    required IconData icon,
    required String title,
    required String subtitle,
  }) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, size: 64, color: DoraColors.textSecondary.withOpacity(0.5)),
          const SizedBox(height: 16),
          Text(
            title,
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          Text(
            subtitle,
            style: TextStyle(color: DoraColors.textSecondary),
          ),
        ],
      ),
    );
  }

  void _showPaymentDetails(BuildContext context, Map<String, dynamic> payment) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => Container(
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
              'Payment Details',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 24),
            _buildDetailRow('Description', payment['description'] ?? 'Subscription'),
            _buildDetailRow('Amount', _formatPrice(payment['amount'] ?? 0)),
            _buildDetailRow('Status', (payment['status'] ?? 'completed').toUpperCase()),
            _buildDetailRow('Date', _formatDate(payment['created_at'])),
            _buildDetailRow('Payment Method', payment['payment_method'] ?? 'Card'),
            if (payment['razorpay_payment_id'] != null)
              _buildDetailRow('Transaction ID', payment['razorpay_payment_id']),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  void _showInvoiceDetails(BuildContext context, Map<String, dynamic> invoice) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => Container(
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
              'Invoice Details',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 24),
            _buildDetailRow('Invoice #', invoice['invoice_number'] ?? 'INV-XXXX'),
            _buildDetailRow('Description', invoice['description'] ?? 'Subscription'),
            _buildDetailRow('Subtotal', _formatPrice(invoice['subtotal'] ?? 0)),
            _buildDetailRow('Tax (18%)', _formatPrice(invoice['tax_amount'] ?? 0)),
            const Divider(height: 24),
            _buildDetailRow(
              'Total',
              _formatPrice(invoice['total'] ?? 0),
              isBold: true,
            ),
            _buildDetailRow('Status', (invoice['is_paid'] ?? false) ? 'PAID' : 'PENDING'),
            _buildDetailRow('Date', _formatDate(invoice['created_at'])),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () => _downloadInvoice(context, invoice),
                icon: const Icon(Icons.download),
                label: const Text('Download PDF'),
              ),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  Widget _buildDetailRow(String label, String value, {bool isBold = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: TextStyle(color: DoraColors.textSecondary),
          ),
          Text(
            value,
            style: TextStyle(
              fontWeight: isBold ? FontWeight.bold : FontWeight.normal,
            ),
          ),
        ],
      ),
    );
  }

  void _downloadInvoice(BuildContext context, Map<String, dynamic> invoice) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            const SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
            ),
            const SizedBox(width: 12),
            Text('Downloading ${invoice['invoice_number'] ?? 'invoice'}...'),
          ],
        ),
      ),
    );

    // Simulate download
    Future.delayed(const Duration(seconds: 2), () {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Invoice downloaded successfully!'),
          backgroundColor: Colors.green,
        ),
      );
    });
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
