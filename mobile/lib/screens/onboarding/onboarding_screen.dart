import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../theme.dart';
import '../register_screen.dart';
import '../login_screen.dart';

class OnboardingScreen extends ConsumerStatefulWidget {
  const OnboardingScreen({super.key});

  @override
  ConsumerState<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends ConsumerState<OnboardingScreen> {
  final PageController _pageController = PageController();
  int _currentPage = 0;

  final List<OnboardingPage> _pages = [
    OnboardingPage(
      title: 'Medical Knowledge at Your Fingertips',
      description: 'Access evidence-based clinical information instantly. '
          'Ask any medical question and get accurate, cited answers.',
      icon: Icons.medical_information,
      gradient: [Color(0xFF4A90D9), Color(0xFF6B73FF)],
    ),
    OnboardingPage(
      title: 'Voice-First Experience',
      description: 'Say "Hey DocAssist" to query hands-free. Perfect for '
          'busy clinical environments when your hands are occupied.',
      icon: Icons.mic,
      gradient: [Color(0xFF11998E), Color(0xFF38EF7D)],
    ),
    OnboardingPage(
      title: '50+ Medical Calculators',
      description: 'From GFR to CHADS2-VASc, all essential calculators '
          'built-in with automatic patient context integration.',
      icon: Icons.calculate,
      gradient: [Color(0xFFFF6B6B), Color(0xFFFFE66D)],
    ),
    OnboardingPage(
      title: 'Works Offline',
      description: 'Critical features work without internet. Perfect for '
          'rural areas or hospital basements with poor connectivity.',
      icon: Icons.cloud_off,
      gradient: [Color(0xFF8E2DE2), Color(0xFF4A00E0)],
    ),
    OnboardingPage(
      title: 'Earn CME Credits',
      description: 'Learn as you work. Every query is a learning opportunity. '
          'Track your progress and earn continuing education credits.',
      icon: Icons.school,
      gradient: [Color(0xFFFF416C), Color(0xFFFF4B2B)],
    ),
  ];

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: PageView.builder(
                controller: _pageController,
                itemCount: _pages.length,
                onPageChanged: (index) {
                  setState(() => _currentPage = index);
                },
                itemBuilder: (context, index) {
                  return _buildPage(_pages[index]);
                },
              ),
            ),
            _buildIndicators(),
            _buildButtons(),
          ],
        ),
      ),
    );
  }

  Widget _buildPage(OnboardingPage page) {
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 120,
            height: 120,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: page.gradient,
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(30),
              boxShadow: [
                BoxShadow(
                  color: page.gradient.first.withOpacity(0.3),
                  blurRadius: 20,
                  offset: const Offset(0, 10),
                ),
              ],
            ),
            child: Icon(
              page.icon,
              size: 60,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 48),
          Text(
            page.title,
            style: const TextStyle(
              fontSize: 28,
              fontWeight: FontWeight.bold,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
          Text(
            page.description,
            style: TextStyle(
              fontSize: 16,
              color: DoraColors.textSecondary,
              height: 1.5,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildIndicators() {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 24),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: List.generate(
          _pages.length,
          (index) => AnimatedContainer(
            duration: const Duration(milliseconds: 300),
            margin: const EdgeInsets.symmetric(horizontal: 4),
            width: _currentPage == index ? 24 : 8,
            height: 8,
            decoration: BoxDecoration(
              color: _currentPage == index
                  ? DoraColors.primary
                  : DoraColors.borderColor,
              borderRadius: BorderRadius.circular(4),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildButtons() {
    final isLastPage = _currentPage == _pages.length - 1;

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: isLastPage ? _goToSignUp : _nextPage,
              style: ElevatedButton.styleFrom(
                backgroundColor: DoraColors.primary,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: Text(
                isLastPage ? 'Get Started' : 'Next',
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
            ),
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (!isLastPage)
                TextButton(
                  onPressed: _goToSignUp,
                  child: Text(
                    'Skip',
                    style: TextStyle(color: DoraColors.textSecondary),
                  ),
                ),
              if (isLastPage) ...[
                Text(
                  'Already have an account? ',
                  style: TextStyle(color: DoraColors.textSecondary),
                ),
                TextButton(
                  onPressed: _goToLogin,
                  child: Text(
                    'Sign In',
                    style: TextStyle(
                      color: DoraColors.primary,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }

  void _nextPage() {
    _pageController.nextPage(
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
    );
  }

  void _goToSignUp() {
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (_) => const RegisterScreen()),
    );
  }

  void _goToLogin() {
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (_) => const LoginScreen()),
    );
  }
}

class OnboardingPage {
  final String title;
  final String description;
  final IconData icon;
  final List<Color> gradient;

  OnboardingPage({
    required this.title,
    required this.description,
    required this.icon,
    required this.gradient,
  });
}
