import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class DoraColors {
  // Primary
  static const Color primary = Color(0xFF0066CC);
  static const Color primaryLight = Color(0xFF4D94FF);
  static const Color primaryDark = Color(0xFF004C99);

  // Backgrounds
  static const Color bgPrimary = Color(0xFFFFFFFF);
  static const Color bgSecondary = Color(0xFFF5F7FA);
  static const Color bgTertiary = Color(0xFFE8ECF0);
  static const Color bgDark = Color(0xFF1C1C1E);

  // Text
  static const Color textPrimary = Color(0xFF1C1C1E);
  static const Color textSecondary = Color(0xFF6B7280);
  static const Color textTertiary = Color(0xFF9CA3AF);
  static const Color textInverse = Color(0xFFFFFFFF);

  // Status
  static const Color success = Color(0xFF10B981);
  static const Color warning = Color(0xFFF59E0B);
  static const Color error = Color(0xFFEF4444);
  static const Color info = Color(0xFF3B82F6);

  // Severity (Drug Interactions)
  static const Color contraindicated = Color(0xFFDC2626);
  static const Color severe = Color(0xFFEA580C);
  static const Color moderate = Color(0xFFD97706);
  static const Color mild = Color(0xFF65A30D);
}

class DoraTheme {
  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      primaryColor: DoraColors.primary,
      scaffoldBackgroundColor: DoraColors.bgSecondary,
      colorScheme: const ColorScheme.light(
        primary: DoraColors.primary,
        onPrimary: DoraColors.textInverse,
        secondary: DoraColors.primaryLight,
        surface: DoraColors.bgPrimary,
        background: DoraColors.bgSecondary,
        error: DoraColors.error,
      ),
      textTheme: GoogleFonts.interTextTheme().copyWith(
        displayLarge: const TextStyle(
          fontSize: 34,
          fontWeight: FontWeight.bold,
          color: DoraColors.textPrimary,
        ),
        displayMedium: const TextStyle(
          fontSize: 28,
          fontWeight: FontWeight.bold,
          color: DoraColors.textPrimary,
        ),
        titleLarge: const TextStyle(
          fontSize: 20,
          fontWeight: FontWeight.w600,
          color: DoraColors.textPrimary,
        ),
        titleMedium: const TextStyle(
          fontSize: 17,
          fontWeight: FontWeight.w600,
          color: DoraColors.textPrimary,
        ),
        bodyLarge: const TextStyle(
          fontSize: 17,
          color: DoraColors.textPrimary,
        ),
        bodyMedium: const TextStyle(
          fontSize: 15,
          color: DoraColors.textPrimary,
        ),
        bodySmall: const TextStyle(
          fontSize: 13,
          color: DoraColors.textSecondary,
        ),
        labelSmall: const TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w600,
          color: DoraColors.textTertiary,
        ),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: DoraColors.bgPrimary,
        foregroundColor: DoraColors.textPrimary,
        elevation: 0,
        centerTitle: true,
      ),
      cardTheme: CardTheme(
        color: DoraColors.bgPrimary,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: DoraColors.primary,
          foregroundColor: DoraColors.textInverse,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: DoraColors.bgPrimary,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: DoraColors.bgTertiary),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: DoraColors.bgTertiary),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: DoraColors.primary, width: 2),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: DoraColors.bgPrimary,
        selectedItemColor: DoraColors.primary,
        unselectedItemColor: DoraColors.textTertiary,
        type: BottomNavigationBarType.fixed,
        elevation: 8,
      ),
    );
  }

  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      primaryColor: DoraColors.primaryLight,
      scaffoldBackgroundColor: DoraColors.bgDark,
      colorScheme: const ColorScheme.dark(
        primary: DoraColors.primaryLight,
        onPrimary: DoraColors.textPrimary,
        secondary: DoraColors.primary,
        surface: Color(0xFF2C2C2E),
        background: DoraColors.bgDark,
        error: DoraColors.error,
      ),
      textTheme: GoogleFonts.interTextTheme(ThemeData.dark().textTheme),
      appBarTheme: const AppBarTheme(
        backgroundColor: DoraColors.bgDark,
        foregroundColor: DoraColors.textInverse,
        elevation: 0,
        centerTitle: true,
      ),
      cardTheme: CardTheme(
        color: const Color(0xFF2C2C2E),
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
      ),
    );
  }
}
