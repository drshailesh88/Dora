/// Example: Flutter mobile app integration with i18n
///
/// This shows how to use the localization system in Flutter applications.
///
/// Setup:
/// 1. Add dependencies to pubspec.yaml:
///    dependencies:
///      flutter:
///        sdk: flutter
///      flutter_localizations:
///        sdk: flutter
///      intl: ^0.18.0
///
/// 2. Add l10n.yaml configuration (already created)
///
/// 3. Run: flutter gen-l10n
///
/// 4. Import and use as shown below

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
// Import generated localizations
// import 'package:dora/generated/l10n/app_localizations.dart';

/// Main app with localization support
class DoraApp extends StatelessWidget {
  const DoraApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Dora',

      // Localization delegates
      localizationsDelegates: const [
        // AppLocalizations.delegate, // Generated from ARB files
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],

      // Supported locales
      supportedLocales: const [
        Locale('en', ''), // English
        Locale('hi', ''), // Hindi
        Locale('mr', ''), // Marathi
        Locale('ta', ''), // Tamil
        Locale('te', ''), // Telugu
        Locale('bn', ''), // Bengali
      ],

      // Locale resolution strategy
      localeResolutionCallback: (locale, supportedLocales) {
        // Check if the current device locale is supported
        for (var supportedLocale in supportedLocales) {
          if (supportedLocale.languageCode == locale?.languageCode) {
            return supportedLocale;
          }
        }
        // Fallback to English
        return const Locale('en', '');
      },

      home: const HomePage(),
    );
  }
}

/// Home page example with localized strings
class HomePage extends StatefulWidget {
  const HomePage({Key? key}) : super(key: key);

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  int _selectedIndex = 0;

  @override
  Widget build(BuildContext context) {
    // Access localizations - uncomment after running flutter gen-l10n
    // final localizations = AppLocalizations.of(context)!;

    // For this example, we'll use placeholder text
    // In production, replace with: localizations.home, etc.

    return Scaffold(
      appBar: AppBar(
        // title: Text(localizations.appName),
        title: const Text('Dora'),
        actions: [
          // Language selector
          IconButton(
            icon: const Icon(Icons.language),
            onPressed: () => _showLanguageSelector(context),
          ),
        ],
      ),

      body: IndexedStack(
        index: _selectedIndex,
        children: const [
          HomeScreen(),
          SearchScreen(),
          LibraryScreen(),
          FavoritesScreen(),
          SettingsScreen(),
        ],
      ),

      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (index) {
          setState(() {
            _selectedIndex = index;
          });
        },
        destinations: const [
          // NavigationDestination(
          //   icon: Icon(Icons.home_outlined),
          //   selectedIcon: Icon(Icons.home),
          //   label: localizations.home,
          // ),
          NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home),
            label: 'Home',
          ),
          NavigationDestination(
            icon: Icon(Icons.search_outlined),
            selectedIcon: Icon(Icons.search),
            label: 'Search',
          ),
          NavigationDestination(
            icon: Icon(Icons.library_books_outlined),
            selectedIcon: Icon(Icons.library_books),
            label: 'Library',
          ),
          NavigationDestination(
            icon: Icon(Icons.favorite_outlined),
            selectedIcon: Icon(Icons.favorite),
            label: 'Favorites',
          ),
          NavigationDestination(
            icon: Icon(Icons.settings_outlined),
            selectedIcon: Icon(Icons.settings),
            label: 'Settings',
          ),
        ],
      ),
    );
  }

  void _showLanguageSelector(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (context) => const LanguageSelectorSheet(),
    );
  }
}

/// Language selector bottom sheet
class LanguageSelectorSheet extends StatelessWidget {
  const LanguageSelectorSheet({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // final localizations = AppLocalizations.of(context)!;

    final languages = [
      {'code': 'en', 'name': 'English', 'nativeName': 'English'},
      {'code': 'hi', 'name': 'Hindi', 'nativeName': 'हिंदी'},
      {'code': 'mr', 'name': 'Marathi', 'nativeName': 'मराठी'},
      {'code': 'ta', 'name': 'Tamil', 'nativeName': 'தமிழ்'},
      {'code': 'te', 'name': 'Telugu', 'nativeName': 'తెలుగు'},
      {'code': 'bn', 'name': 'Bengali', 'nativeName': 'বাংলা'},
    ];

    return Container(
      padding: const EdgeInsets.all(16),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Text(
          //   localizations.language,
          //   style: Theme.of(context).textTheme.headlineSmall,
          // ),
          Text(
            'Language',
            style: Theme.of(context).textTheme.headlineSmall,
          ),
          const SizedBox(height: 16),
          ...languages.map((lang) => ListTile(
            title: Text(lang['nativeName']!),
            subtitle: Text(lang['name']!),
            onTap: () {
              // Change locale - in production, save to preferences
              // and rebuild app with new locale
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text('Language changed to ${lang['nativeName']}'),
                ),
              );
            },
          )),
        ],
      ),
    );
  }
}

/// Home screen with medical query
class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final TextEditingController _queryController = TextEditingController();
  String? _response;
  bool _isLoading = false;

  @override
  Widget build(BuildContext context) {
    // final localizations = AppLocalizations.of(context)!;

    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Welcome message
          // Text(
          //   localizations.greetingMorning('Dr. Sharma'),
          //   style: Theme.of(context).textTheme.headlineMedium,
          // ),
          Text(
            'Good morning, Dr. Sharma',
            style: Theme.of(context).textTheme.headlineMedium,
          ),
          const SizedBox(height: 24),

          // Query input
          TextField(
            controller: _queryController,
            // decoration: InputDecoration(
            //   hintText: localizations.askQuestion,
            //   border: const OutlineInputBorder(),
            // ),
            decoration: const InputDecoration(
              hintText: 'Ask your medical question...',
              border: OutlineInputBorder(),
            ),
            maxLines: 3,
          ),
          const SizedBox(height: 16),

          // Submit button
          ElevatedButton.icon(
            // onPressed: _isLoading ? null : _submitQuery,
            onPressed: null, // Disabled in example
            icon: _isLoading
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.send),
            // label: Text(_isLoading
            //     ? localizations.processing
            //     : localizations.submit),
            label: const Text('Submit'),
          ),

          // Response
          if (_response != null) ...[
            const SizedBox(height: 24),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Warning banner
                    // Container(
                    //   padding: const EdgeInsets.all(8),
                    //   color: Colors.amber.shade100,
                    //   child: Row(
                    //     children: [
                    //       const Icon(Icons.warning_amber, size: 20),
                    //       const SizedBox(width: 8),
                    //       Expanded(
                    //         child: Text(
                    //           localizations.draftWarning,
                    //           style: const TextStyle(fontSize: 12),
                    //         ),
                    //       ),
                    //     ],
                    //   ),
                    // ),
                    const SizedBox(height: 16),
                    Text(_response!),
                  ],
                ),
              ),
            ),
          ],

          // Medical terms quick access
          const SizedBox(height: 24),
          // Text(
          //   localizations.relatedTopics,
          //   style: Theme.of(context).textTheme.titleMedium,
          // ),
          Text(
            'Common Medical Terms',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            children: [
              // Chip(label: Text(localizations.diabetes)),
              // Chip(label: Text(localizations.hypertension)),
              // Chip(label: Text(localizations.fever)),
              const Chip(label: Text('Diabetes')),
              const Chip(label: Text('Hypertension')),
              const Chip(label: Text('Fever')),
            ],
          ),
        ],
      ),
    );
  }

  // void _submitQuery() async {
  //   setState(() {
  //     _isLoading = true;
  //   });
  //
  //   // Simulate API call
  //   await Future.delayed(const Duration(seconds: 2));
  //
  //   setState(() {
  //     _response = 'Sample response...';
  //     _isLoading = false;
  //   });
  // }

  @override
  void dispose() {
    _queryController.dispose();
    super.dispose();
  }
}

/// Placeholder screens
class SearchScreen extends StatelessWidget {
  const SearchScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return const Center(child: Text('Search Screen'));
  }
}

class LibraryScreen extends StatelessWidget {
  const LibraryScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return const Center(child: Text('Library Screen'));
  }
}

class FavoritesScreen extends StatelessWidget {
  const FavoritesScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return const Center(child: Text('Favorites Screen'));
  }
}

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return const Center(child: Text('Settings Screen'));
  }
}

/// Main entry point
void main() {
  runApp(const DoraApp());
}
