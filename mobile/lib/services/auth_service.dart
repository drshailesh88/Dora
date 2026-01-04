import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hive/hive.dart';
import 'package:dio/dio.dart';

// Auth state
enum AuthStatus { initial, authenticated, unauthenticated, loading }

class AuthState {
  final AuthStatus status;
  final User? user;
  final String? error;

  const AuthState({
    this.status = AuthStatus.initial,
    this.user,
    this.error,
  });

  AuthState copyWith({
    AuthStatus? status,
    User? user,
    String? error,
  }) {
    return AuthState(
      status: status ?? this.status,
      user: user ?? this.user,
      error: error,
    );
  }
}

class User {
  final String id;
  final String email;
  final String name;
  final String role;
  final String? specialty;
  final String? institution;
  final bool isVerified;
  final bool emailVerified;
  final bool mfaEnabled;
  final String licenseTier;
  final String? avatarUrl;

  const User({
    required this.id,
    required this.email,
    required this.name,
    required this.role,
    this.specialty,
    this.institution,
    this.isVerified = false,
    this.emailVerified = false,
    this.mfaEnabled = false,
    this.licenseTier = 'FREE',
    this.avatarUrl,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] as String,
      email: json['email'] as String,
      name: json['name'] as String,
      role: json['role'] as String,
      specialty: json['specialty'] as String?,
      institution: json['institution'] as String?,
      isVerified: json['is_verified'] as bool? ?? false,
      emailVerified: json['email_verified'] as bool? ?? false,
      mfaEnabled: json['mfa_enabled'] as bool? ?? false,
      licenseTier: json['license_tier'] as String? ?? 'FREE',
      avatarUrl: json['avatar_url'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'name': name,
      'role': role,
      'specialty': specialty,
      'institution': institution,
      'is_verified': isVerified,
      'email_verified': emailVerified,
      'mfa_enabled': mfaEnabled,
      'license_tier': licenseTier,
      'avatar_url': avatarUrl,
    };
  }
}

class AuthTokens {
  final String accessToken;
  final String refreshToken;
  final int expiresIn;

  const AuthTokens({
    required this.accessToken,
    required this.refreshToken,
    required this.expiresIn,
  });

  factory AuthTokens.fromJson(Map<String, dynamic> json) {
    return AuthTokens(
      accessToken: json['access_token'] as String,
      refreshToken: json['refresh_token'] as String,
      expiresIn: json['expires_in'] as int,
    );
  }
}

class AuthService {
  final Dio _dio;
  final Box _storage;

  static const _accessTokenKey = 'access_token';
  static const _refreshTokenKey = 'refresh_token';
  static const _userKey = 'user';

  AuthService({required Dio dio, required Box storage})
      : _dio = dio,
        _storage = storage {
    _setupInterceptors();
  }

  void _setupInterceptors() {
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await getAccessToken();
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (error, handler) async {
        if (error.response?.statusCode == 401) {
          // Try to refresh token
          final refreshed = await _refreshTokens();
          if (refreshed) {
            // Retry original request
            final opts = error.requestOptions;
            final token = await getAccessToken();
            opts.headers['Authorization'] = 'Bearer $token';
            final response = await _dio.fetch(opts);
            handler.resolve(response);
            return;
          }
        }
        handler.next(error);
      },
    ));
  }

  // Storage methods
  Future<String?> getAccessToken() async {
    return _storage.get(_accessTokenKey) as String?;
  }

  Future<String?> getRefreshToken() async {
    return _storage.get(_refreshTokenKey) as String?;
  }

  Future<void> _saveTokens(AuthTokens tokens) async {
    await _storage.put(_accessTokenKey, tokens.accessToken);
    await _storage.put(_refreshTokenKey, tokens.refreshToken);
  }

  Future<void> _saveUser(User user) async {
    await _storage.put(_userKey, jsonEncode(user.toJson()));
  }

  Future<User?> getSavedUser() async {
    final data = _storage.get(_userKey) as String?;
    if (data != null) {
      return User.fromJson(jsonDecode(data) as Map<String, dynamic>);
    }
    return null;
  }

  Future<void> _clearAuth() async {
    await _storage.delete(_accessTokenKey);
    await _storage.delete(_refreshTokenKey);
    await _storage.delete(_userKey);
  }

  // Auth methods
  Future<(User?, String?)> register({
    required String email,
    required String password,
    required String name,
    String role = 'doctor',
    String? specialty,
    String? institution,
    String? registrationNumber,
  }) async {
    try {
      final response = await _dio.post('/api/v1/auth/register', data: {
        'email': email,
        'password': password,
        'name': name,
        'role': role,
        'specialty': specialty,
        'institution': institution,
        'registration_number': registrationNumber,
      });

      final user = User.fromJson(response.data as Map<String, dynamic>);
      return (user, null);
    } on DioException catch (e) {
      final message = e.response?.data?['detail'] as String? ?? 'Registration failed';
      return (null, message);
    }
  }

  Future<(User?, String?)> login({
    required String email,
    required String password,
  }) async {
    try {
      final response = await _dio.post('/api/v1/auth/login', data: {
        'email': email,
        'password': password,
      });

      final data = response.data as Map<String, dynamic>;

      if (data['requires_mfa'] == true) {
        return (null, 'MFA required');
      }

      final tokens = AuthTokens.fromJson(data);
      final user = User.fromJson(data['user'] as Map<String, dynamic>);

      await _saveTokens(tokens);
      await _saveUser(user);

      return (user, null);
    } on DioException catch (e) {
      final message = e.response?.data?['detail'] as String? ?? 'Login failed';
      return (null, message);
    }
  }

  Future<bool> _refreshTokens() async {
    try {
      final refreshToken = await getRefreshToken();
      if (refreshToken == null) return false;

      final response = await _dio.post('/api/v1/auth/refresh', data: {
        'refresh_token': refreshToken,
      });

      final data = response.data as Map<String, dynamic>;
      final tokens = AuthTokens.fromJson(data);
      final user = User.fromJson(data['user'] as Map<String, dynamic>);

      await _saveTokens(tokens);
      await _saveUser(user);

      return true;
    } catch (e) {
      await _clearAuth();
      return false;
    }
  }

  Future<void> logout() async {
    try {
      final refreshToken = await getRefreshToken();
      if (refreshToken != null) {
        await _dio.post('/api/v1/auth/logout', data: {
          'refresh_token': refreshToken,
        });
      }
    } catch (e) {
      // Ignore logout errors
    } finally {
      await _clearAuth();
    }
  }

  Future<User?> getCurrentUser() async {
    try {
      final response = await _dio.get('/api/v1/auth/me');
      final user = User.fromJson(response.data as Map<String, dynamic>);
      await _saveUser(user);
      return user;
    } catch (e) {
      return await getSavedUser();
    }
  }

  Future<(User?, String?)> updateProfile({
    String? name,
    String? specialty,
    String? institution,
    String? phone,
  }) async {
    try {
      final response = await _dio.patch('/api/v1/auth/me', data: {
        if (name != null) 'name': name,
        if (specialty != null) 'specialty': specialty,
        if (institution != null) 'institution': institution,
        if (phone != null) 'phone': phone,
      });

      final user = User.fromJson(response.data as Map<String, dynamic>);
      await _saveUser(user);
      return (user, null);
    } on DioException catch (e) {
      final message = e.response?.data?['detail'] as String? ?? 'Update failed';
      return (null, message);
    }
  }

  Future<(bool, String)> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    try {
      await _dio.post('/api/v1/auth/change-password', data: {
        'current_password': currentPassword,
        'new_password': newPassword,
      });
      return (true, 'Password changed successfully');
    } on DioException catch (e) {
      final message = e.response?.data?['detail'] as String? ?? 'Failed to change password';
      return (false, message);
    }
  }

  Future<(bool, String)> requestPasswordReset(String email) async {
    try {
      await _dio.post('/api/v1/auth/forgot-password', data: {
        'email': email,
      });
      return (true, 'If the email exists, a reset link has been sent');
    } on DioException catch (e) {
      final message = e.response?.data?['detail'] as String? ?? 'Failed to send reset email';
      return (false, message);
    }
  }

  // SSO methods
  Future<(String?, String?)> initSSO(String provider, String redirectUri) async {
    try {
      final response = await _dio.post('/api/v1/auth/sso/init', data: {
        'provider': provider,
        'redirect_uri': redirectUri,
      });
      final url = response.data['authorization_url'] as String;
      final state = response.data['state'] as String;
      return (url, state);
    } catch (e) {
      return (null, null);
    }
  }

  Future<(User?, String?)> handleSSOCallback(String state, String code) async {
    try {
      final response = await _dio.post('/api/v1/auth/sso/callback', data: {
        'state': state,
        'code': code,
      });

      final data = response.data as Map<String, dynamic>;
      final tokens = AuthTokens.fromJson(data);
      final user = User.fromJson(data['user'] as Map<String, dynamic>);

      await _saveTokens(tokens);
      await _saveUser(user);

      return (user, null);
    } on DioException catch (e) {
      final message = e.response?.data?['detail'] as String? ?? 'SSO failed';
      return (null, message);
    }
  }
}

// Providers
final authServiceProvider = Provider<AuthService>((ref) {
  throw UnimplementedError('AuthService must be overridden in main()');
});

class AuthNotifier extends StateNotifier<AuthState> {
  final AuthService _authService;

  AuthNotifier(this._authService) : super(const AuthState()) {
    _checkAuth();
  }

  Future<void> _checkAuth() async {
    state = state.copyWith(status: AuthStatus.loading);

    final user = await _authService.getCurrentUser();
    if (user != null) {
      state = state.copyWith(
        status: AuthStatus.authenticated,
        user: user,
      );
    } else {
      state = state.copyWith(status: AuthStatus.unauthenticated);
    }
  }

  Future<void> register({
    required String email,
    required String password,
    required String name,
    String role = 'doctor',
    String? specialty,
    String? institution,
  }) async {
    state = state.copyWith(status: AuthStatus.loading);

    final (user, error) = await _authService.register(
      email: email,
      password: password,
      name: name,
      role: role,
      specialty: specialty,
      institution: institution,
    );

    if (user != null) {
      // Registration successful, but need to login
      state = state.copyWith(
        status: AuthStatus.unauthenticated,
        error: null,
      );
    } else {
      state = state.copyWith(
        status: AuthStatus.unauthenticated,
        error: error,
      );
    }
  }

  Future<void> login({required String email, required String password}) async {
    state = state.copyWith(status: AuthStatus.loading);

    final (user, error) = await _authService.login(
      email: email,
      password: password,
    );

    if (user != null) {
      state = state.copyWith(
        status: AuthStatus.authenticated,
        user: user,
        error: null,
      );
    } else {
      state = state.copyWith(
        status: AuthStatus.unauthenticated,
        error: error,
      );
    }
  }

  Future<void> logout() async {
    await _authService.logout();
    state = const AuthState(status: AuthStatus.unauthenticated);
  }

  void clearError() {
    state = state.copyWith(error: null);
  }
}

final authStateProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  final authService = ref.watch(authServiceProvider);
  return AuthNotifier(authService);
});

final isAuthenticatedProvider = Provider<bool>((ref) {
  final authState = ref.watch(authStateProvider);
  return authState.status == AuthStatus.authenticated;
});

final currentUserProvider = Provider<User?>((ref) {
  final authState = ref.watch(authStateProvider);
  return authState.user;
});
