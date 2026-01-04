import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../theme.dart';
import '../../providers/auth_provider.dart';
import '../home_screen.dart';

class SpecialtySelectionScreen extends ConsumerStatefulWidget {
  const SpecialtySelectionScreen({super.key});

  @override
  ConsumerState<SpecialtySelectionScreen> createState() => _SpecialtySelectionScreenState();
}

class _SpecialtySelectionScreenState extends ConsumerState<SpecialtySelectionScreen> {
  String? _selectedSpecialty;
  final List<String> _selectedInterests = [];

  final List<Map<String, dynamic>> _specialties = [
    {'id': 'general', 'name': 'General Medicine', 'icon': Icons.medical_services},
    {'id': 'cardiology', 'name': 'Cardiology', 'icon': Icons.favorite},
    {'id': 'neurology', 'name': 'Neurology', 'icon': Icons.psychology},
    {'id': 'pulmonology', 'name': 'Pulmonology', 'icon': Icons.air},
    {'id': 'gastroenterology', 'name': 'Gastroenterology', 'icon': Icons.healing},
    {'id': 'nephrology', 'name': 'Nephrology', 'icon': Icons.water_drop},
    {'id': 'endocrinology', 'name': 'Endocrinology', 'icon': Icons.science},
    {'id': 'rheumatology', 'name': 'Rheumatology', 'icon': Icons.accessibility},
    {'id': 'infectious', 'name': 'Infectious Disease', 'icon': Icons.coronavirus},
    {'id': 'oncology', 'name': 'Oncology', 'icon': Icons.biotech},
    {'id': 'pediatrics', 'name': 'Pediatrics', 'icon': Icons.child_care},
    {'id': 'emergency', 'name': 'Emergency Medicine', 'icon': Icons.emergency},
    {'id': 'surgery', 'name': 'Surgery', 'icon': Icons.content_cut},
    {'id': 'orthopedics', 'name': 'Orthopedics', 'icon': Icons.accessibility_new},
    {'id': 'dermatology', 'name': 'Dermatology', 'icon': Icons.spa},
    {'id': 'psychiatry', 'name': 'Psychiatry', 'icon': Icons.self_improvement},
  ];

  final List<String> _interests = [
    'Drug Interactions',
    'Clinical Trials',
    'Evidence-Based Medicine',
    'Medical Guidelines',
    'Patient Education',
    'Academic Writing',
    'CME/Learning',
    'Rare Diseases',
    'Preventive Care',
    'Critical Care',
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Personalize Dora'),
        backgroundColor: DoraColors.bgPrimary,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'What\'s your specialty?',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              'This helps us personalize your experience',
              style: TextStyle(color: DoraColors.textSecondary),
            ),
            const SizedBox(height: 24),
            _buildSpecialtyGrid(),
            const SizedBox(height: 32),
            const Text(
              'What are you interested in?',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              'Select all that apply',
              style: TextStyle(color: DoraColors.textSecondary),
            ),
            const SizedBox(height: 16),
            _buildInterestChips(),
            const SizedBox(height: 32),
            _buildContinueButton(),
          ],
        ),
      ),
    );
  }

  Widget _buildSpecialtyGrid() {
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        childAspectRatio: 2.5,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
      ),
      itemCount: _specialties.length,
      itemBuilder: (context, index) {
        final specialty = _specialties[index];
        final isSelected = _selectedSpecialty == specialty['id'];

        return InkWell(
          onTap: () => setState(() => _selectedSpecialty = specialty['id']),
          borderRadius: BorderRadius.circular(12),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: isSelected
                  ? DoraColors.primary.withOpacity(0.1)
                  : DoraColors.bgSecondary,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: isSelected ? DoraColors.primary : DoraColors.borderColor,
                width: isSelected ? 2 : 1,
              ),
            ),
            child: Row(
              children: [
                Icon(
                  specialty['icon'],
                  color: isSelected ? DoraColors.primary : DoraColors.textSecondary,
                  size: 20,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    specialty['name'],
                    style: TextStyle(
                      fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                      color: isSelected ? DoraColors.primary : DoraColors.textPrimary,
                      fontSize: 12,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                if (isSelected)
                  Icon(Icons.check_circle, color: DoraColors.primary, size: 18),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildInterestChips() {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: _interests.map((interest) {
        final isSelected = _selectedInterests.contains(interest);

        return FilterChip(
          selected: isSelected,
          label: Text(interest),
          selectedColor: DoraColors.primary.withOpacity(0.2),
          checkmarkColor: DoraColors.primary,
          backgroundColor: DoraColors.bgSecondary,
          labelStyle: TextStyle(
            color: isSelected ? DoraColors.primary : DoraColors.textPrimary,
          ),
          side: BorderSide(
            color: isSelected ? DoraColors.primary : DoraColors.borderColor,
          ),
          onSelected: (selected) {
            setState(() {
              if (selected) {
                _selectedInterests.add(interest);
              } else {
                _selectedInterests.remove(interest);
              }
            });
          },
        );
      }).toList(),
    );
  }

  Widget _buildContinueButton() {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton(
        onPressed: _selectedSpecialty != null ? _continue : null,
        style: ElevatedButton.styleFrom(
          backgroundColor: DoraColors.primary,
          disabledBackgroundColor: DoraColors.borderColor,
          padding: const EdgeInsets.symmetric(vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
        child: const Text(
          'Continue',
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
      ),
    );
  }

  Future<void> _continue() async {
    // Save preferences
    await ref.read(userPreferencesProvider.notifier).updatePreferences({
      'specialty': _selectedSpecialty,
      'interests': _selectedInterests,
    });

    if (mounted) {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const HomeScreen()),
      );
    }
  }
}

// Provider for user preferences
final userPreferencesProvider = StateNotifierProvider<UserPreferencesNotifier, Map<String, dynamic>>(
  (ref) => UserPreferencesNotifier(),
);

class UserPreferencesNotifier extends StateNotifier<Map<String, dynamic>> {
  UserPreferencesNotifier() : super({});

  Future<void> updatePreferences(Map<String, dynamic> prefs) async {
    state = {...state, ...prefs};
    // TODO: Save to API
  }
}
