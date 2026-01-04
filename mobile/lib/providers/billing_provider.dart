/// Billing Providers
///
/// State management for subscriptions, payments, and billing.

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'auth_provider.dart';

/// Current subscription provider
final currentSubscriptionProvider = FutureProvider<Map<String, dynamic>?>((ref) async {
  final token = await ref.watch(accessTokenProvider.future);
  if (token == null) return null;

  try {
    final response = await http.get(
      Uri.parse('https://api.dora.app/api/v1/payments/subscriptions/current'),
      headers: {'Authorization': 'Bearer $token'},
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else if (response.statusCode == 404) {
      return null; // No subscription
    }
    return null;
  } catch (e) {
    // Return mock data for development
    return {
      'id': 'sub_mock123',
      'plan': {
        'id': 'professional',
        'name': 'Professional',
        'description': 'Full access to all medical knowledge features',
      },
      'status': 'active',
      'is_trial': false,
      'amount': 99900,
      'billing_cycle': 'monthly',
      'next_billing_date': DateTime.now().add(Duration(days: 15)).toIso8601String(),
      'usage': {
        'queries': 245,
        'documents': 12,
        'storage_mb': 512,
      },
      'limits': {
        'queries': -1, // Unlimited
        'documents': 100,
        'storage_mb': 5120, // 5GB
      },
      'billing_info': {
        'payment_method': 'Card ending in 4242',
        'email': 'doctor@clinic.com',
        'gstin': '29AABCT1234A1Z5',
      },
    };
  }
});

/// Available plans provider
final availablePlansProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  try {
    final response = await http.get(
      Uri.parse('https://api.dora.app/api/v1/payments/plans'),
    );

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return List<Map<String, dynamic>>.from(data['plans'] ?? []);
    }
    return _getMockPlans();
  } catch (e) {
    return _getMockPlans();
  }
});

List<Map<String, dynamic>> _getMockPlans() {
  return [
    {
      'id': 'basic',
      'name': 'Basic',
      'description': 'Essential features for individual practitioners',
      'price_monthly': 49900,
      'price_quarterly': 134900,
      'price_yearly': 479900,
      'is_recommended': false,
      'is_current': false,
      'features': [
        'Up to 100 queries/month',
        'Basic medical search',
        'Drug interactions check',
        '5 document uploads/month',
        'Email support',
      ],
    },
    {
      'id': 'professional',
      'name': 'Professional',
      'description': 'Full access for busy clinicians',
      'price_monthly': 99900,
      'price_quarterly': 269900,
      'price_yearly': 959900,
      'is_recommended': true,
      'is_current': true,
      'features': [
        'Unlimited queries',
        'Advanced RAG search',
        'Drug dosing calculators',
        'Clinical decision support',
        '100 document uploads/month',
        '5GB storage',
        'Morning briefings',
        'Priority support',
      ],
    },
    {
      'id': 'enterprise',
      'name': 'Enterprise',
      'description': 'For hospitals and large practices',
      'price_monthly': 249900,
      'price_quarterly': 674900,
      'price_yearly': 2399900,
      'is_recommended': false,
      'is_current': false,
      'features': [
        'Everything in Professional',
        'Unlimited team members',
        'EMR integration',
        'Custom protocols',
        'Analytics dashboard',
        'Dedicated account manager',
        'SLA guarantee',
        'On-premise deployment option',
      ],
    },
  ];
}

/// Payment history provider
final paymentHistoryProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final token = await ref.watch(accessTokenProvider.future);
  if (token == null) return {'payments': [], 'invoices': []};

  try {
    final paymentsResponse = await http.get(
      Uri.parse('https://api.dora.app/api/v1/payments/history'),
      headers: {'Authorization': 'Bearer $token'},
    );

    final invoicesResponse = await http.get(
      Uri.parse('https://api.dora.app/api/v1/payments/invoices'),
      headers: {'Authorization': 'Bearer $token'},
    );

    return {
      'payments': paymentsResponse.statusCode == 200
          ? json.decode(paymentsResponse.body)['payments'] ?? []
          : [],
      'invoices': invoicesResponse.statusCode == 200
          ? json.decode(invoicesResponse.body)['invoices'] ?? []
          : [],
    };
  } catch (e) {
    // Return mock data
    return {
      'payments': [
        {
          'id': 'pay_001',
          'description': 'Professional Plan - Monthly',
          'amount': 117882, // Including GST
          'status': 'completed',
          'payment_method': 'Card ending in 4242',
          'created_at': DateTime.now().subtract(Duration(days: 5)).toIso8601String(),
          'razorpay_payment_id': 'pay_ABC123XYZ',
        },
        {
          'id': 'pay_002',
          'description': 'Professional Plan - Monthly',
          'amount': 117882,
          'status': 'completed',
          'payment_method': 'Card ending in 4242',
          'created_at': DateTime.now().subtract(Duration(days: 35)).toIso8601String(),
          'razorpay_payment_id': 'pay_DEF456UVW',
        },
        {
          'id': 'pay_003',
          'description': 'Professional Plan - Monthly',
          'amount': 117882,
          'status': 'completed',
          'payment_method': 'UPI',
          'created_at': DateTime.now().subtract(Duration(days: 65)).toIso8601String(),
          'razorpay_payment_id': 'pay_GHI789RST',
        },
      ],
      'invoices': [
        {
          'id': 'inv_001',
          'invoice_number': 'INV-2026-001',
          'description': 'Professional Plan - Monthly Subscription',
          'subtotal': 99900,
          'tax_amount': 17982,
          'total': 117882,
          'is_paid': true,
          'created_at': DateTime.now().subtract(Duration(days: 5)).toIso8601String(),
        },
        {
          'id': 'inv_002',
          'invoice_number': 'INV-2025-012',
          'description': 'Professional Plan - Monthly Subscription',
          'subtotal': 99900,
          'tax_amount': 17982,
          'total': 117882,
          'is_paid': true,
          'created_at': DateTime.now().subtract(Duration(days: 35)).toIso8601String(),
        },
        {
          'id': 'inv_003',
          'invoice_number': 'INV-2025-011',
          'description': 'Professional Plan - Monthly Subscription',
          'subtotal': 99900,
          'tax_amount': 17982,
          'total': 117882,
          'is_paid': true,
          'created_at': DateTime.now().subtract(Duration(days: 65)).toIso8601String(),
        },
      ],
    };
  }
});

/// Subscription actions notifier
class SubscriptionActionsNotifier extends StateNotifier<AsyncValue<void>> {
  final Ref ref;

  SubscriptionActionsNotifier(this.ref) : super(const AsyncValue.data(null));

  Future<void> subscribe(String planId, String billingCycle) async {
    state = const AsyncValue.loading();
    try {
      final token = await ref.read(accessTokenProvider.future);
      final response = await http.post(
        Uri.parse('https://api.dora.app/api/v1/payments/subscriptions'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
        body: json.encode({
          'plan_id': planId,
          'billing_cycle': billingCycle,
        }),
      );

      if (response.statusCode == 200) {
        state = const AsyncValue.data(null);
        ref.invalidate(currentSubscriptionProvider);
      } else {
        throw Exception('Failed to create subscription');
      }
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> cancel() async {
    state = const AsyncValue.loading();
    try {
      final token = await ref.read(accessTokenProvider.future);
      final subscription = await ref.read(currentSubscriptionProvider.future);

      if (subscription == null) {
        throw Exception('No active subscription');
      }

      final response = await http.post(
        Uri.parse('https://api.dora.app/api/v1/payments/subscriptions/${subscription['id']}/cancel'),
        headers: {'Authorization': 'Bearer $token'},
      );

      if (response.statusCode == 200) {
        state = const AsyncValue.data(null);
        ref.invalidate(currentSubscriptionProvider);
      } else {
        throw Exception('Failed to cancel subscription');
      }
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> changePlan(String newPlanId, String billingCycle) async {
    state = const AsyncValue.loading();
    try {
      final token = await ref.read(accessTokenProvider.future);
      final subscription = await ref.read(currentSubscriptionProvider.future);

      if (subscription == null) {
        throw Exception('No active subscription');
      }

      final response = await http.post(
        Uri.parse('https://api.dora.app/api/v1/payments/subscriptions/${subscription['id']}/change-plan'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
        body: json.encode({
          'plan_id': newPlanId,
          'billing_cycle': billingCycle,
        }),
      );

      if (response.statusCode == 200) {
        state = const AsyncValue.data(null);
        ref.invalidate(currentSubscriptionProvider);
      } else {
        throw Exception('Failed to change plan');
      }
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }
}

final subscriptionActionsProvider =
    StateNotifierProvider<SubscriptionActionsNotifier, AsyncValue<void>>((ref) {
  return SubscriptionActionsNotifier(ref);
});
