import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../theme.dart';
import '../services/api_client.dart';
import 'home_screen.dart';

class SplashScreen extends ConsumerStatefulWidget {
  const SplashScreen({super.key});

  @override
  ConsumerState<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends ConsumerState<SplashScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _fadeAnimation;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    );

    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeIn),
    );

    _scaleAnimation = Tween<double>(begin: 0.8, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOutBack),
    );

    _controller.forward();
    _initializeApp();
  }

  Future<void> _initializeApp() async {
    // Wait for animation
    await Future.delayed(const Duration(seconds: 2));

    // Check API connection
    final client = ref.read(apiClientProvider);
    await client.healthCheck();

    // Navigate to home
    if (mounted) {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => const HomeScreen()),
      );
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: DoraColors.bgPrimary,
      body: Center(
        child: AnimatedBuilder(
          animation: _controller,
          builder: (context, child) {
            return Opacity(
              opacity: _fadeAnimation.value,
              child: Transform.scale(
                scale: _scaleAnimation.value,
                child: child,
              ),
            );
          },
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Logo
              Container(
                width: 100,
                height: 100,
                decoration: BoxDecoration(
                  color: DoraColors.primary,
                  borderRadius: BorderRadius.circular(24),
                  boxShadow: [
                    BoxShadow(
                      color: DoraColors.primary.withOpacity(0.3),
                      blurRadius: 20,
                      offset: const Offset(0, 10),
                    ),
                  ],
                ),
                child: const Icon(
                  Icons.local_hospital,
                  size: 50,
                  color: DoraColors.textInverse,
                ),
              ),
              const SizedBox(height: 24),

              // Title
              Text(
                'Dora',
                style: Theme.of(context).textTheme.displayMedium?.copyWith(
                      color: DoraColors.textPrimary,
                      fontWeight: FontWeight.bold,
                    ),
              ),
              const SizedBox(height: 8),

              // Subtitle
              Text(
                'Medical Knowledge Platform',
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      color: DoraColors.textSecondary,
                    ),
              ),
              const SizedBox(height: 48),

              // Loading indicator
              const SizedBox(
                width: 24,
                height: 24,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  valueColor: AlwaysStoppedAnimation(DoraColors.primary),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
