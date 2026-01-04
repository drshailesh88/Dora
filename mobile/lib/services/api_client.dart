import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/medical_answer.dart';
import '../models/drug_interaction.dart';

/// API client for Dora backend
class DoraApiClient {
  final Dio _dio;

  DoraApiClient({
    Dio? dio,
    String? baseUrl,
  }) : _dio = dio ?? Dio() {
    if (baseUrl != null && dio == null) {
      _dio.options = BaseOptions(
        baseUrl: baseUrl,
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 60),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      );

      // Add interceptors for logging in debug mode
      _dio.interceptors.add(LogInterceptor(
        requestBody: true,
        responseBody: true,
      ));
    }
  }

  /// Health check
  Future<Map<String, dynamic>> healthCheck() async {
    try {
      final response = await _dio.get('/health');
      return response.data;
    } catch (e) {
      return {'status': 'error', 'error': e.toString()};
    }
  }

  /// Query the medical knowledge base
  Future<MedicalAnswer?> query({
    required String question,
    int? patientId,
    int topK = 10,
  }) async {
    try {
      final response = await _dio.post('/api/v1/query', data: {
        'question': question,
        'patient_id': patientId,
        'top_k': topK,
      });

      if (response.data['success'] == true && response.data['answer'] != null) {
        return MedicalAnswer.fromJson(response.data['answer']);
      }
      return null;
    } catch (e) {
      rethrow;
    }
  }

  /// Check drug interactions
  Future<DrugInteractionResult> checkDrugInteractions({
    required List<String> drugs,
    List<String>? patientMedications,
  }) async {
    try {
      final response = await _dio.post('/api/v1/drugs/check', data: {
        'drugs': drugs,
        'patient_medications': patientMedications,
      });

      return DrugInteractionResult.fromJson(response.data);
    } catch (e) {
      return DrugInteractionResult(
        success: false,
        interactions: [],
        warnings: [],
        error: e.toString(),
      );
    }
  }

  /// Normalize drug name
  Future<Map<String, dynamic>?> normalizeDrug(String drugName) async {
    try {
      final response = await _dio.get('/api/v1/drugs/normalize/$drugName');
      return response.data;
    } catch (e) {
      return null;
    }
  }

  /// Get license status
  Future<Map<String, dynamic>> getLicenseStatus() async {
    try {
      final response = await _dio.get('/api/v1/license/status');
      return response.data;
    } catch (e) {
      return {'status': 'error', 'error': e.toString()};
    }
  }

  /// Activate license
  Future<Map<String, dynamic>> activateLicense(String licenseKey) async {
    try {
      final response = await _dio.post('/api/v1/license/activate', data: {
        'license_key': licenseKey,
      });
      return response.data;
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  /// Get knowledge base stats
  Future<Map<String, dynamic>> getStats() async {
    try {
      final response = await _dio.get('/api/v1/stats');
      return response.data;
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }
}

/// Provider for API client
final apiClientProvider = Provider<DoraApiClient>((ref) {
  throw UnimplementedError('DoraApiClient must be overridden in main()');
});

/// Provider for connection status
final connectionStatusProvider = FutureProvider<bool>((ref) async {
  final client = ref.watch(apiClientProvider);
  final health = await client.healthCheck();
  return health['status'] == 'healthy';
});
