import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hive_flutter/hive_flutter.dart';

import 'theme.dart';
import 'services/api_client.dart';
import 'screens/home_screen.dart';
import 'screens/splash_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize Hive for local storage
  await Hive.initFlutter();

  // Set preferred orientations
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  // Set system UI overlay style
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.dark,
    ),
  );

  runApp(
    const ProviderScope(
      child: DoraApp(),
    ),
  );
}

class DoraApp extends ConsumerWidget {
  const DoraApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return MaterialApp(
      title: 'Dora',
      debugShowCheckedModeBanner: false,
      theme: DoraTheme.lightTheme,
      darkTheme: DoraTheme.darkTheme,
      themeMode: ThemeMode.system,
      home: const SplashScreen(),
      routes: {
        '/home': (context) => const HomeScreen(),
      },
    );
  }
}
