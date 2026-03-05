import 'package:flutter/material.dart';

/// Centralized color definitions for the Senzor app
/// Optimized for dark mode OLED displays
class AppColors {
  // Brand Colors
  static const Color primaryBlue = Color(0xFF4FACFE);
  static const Color primaryBlueDark = Color(0xFF2196F3);
  static const Color accentCyan = Color(0xFF00F2FE);
  
  // Background & Surface
  static const Color backgroundDark = Color(0xFF121212);
  static const Color surfaceDark = Color(0xFF1E1E1E);
  static const Color surfaceLight = Color(0xFF2D2D2D);
  
  // Signal Status Colors
  static const Color signalExcellent = Color(0xFF4CAF50);
  static const Color signalGood = Color(0xFF8BC34A);
  static const Color signalFair = Color(0xFFFFC107);
  static const Color signalPoor = Color(0xFFFF5722);
  static const Color signalCritical = Color(0xFFF44336);
  
  // Semantic Colors
  static const Color success = Color(0xFF4CAF50);
  static const Color error = Color(0xFFFF4B2B);
  static const Color warning = Color(0xFFFFC107);
  static const Color info = Color(0xFF2196F3);
  
  // Text Colors
  static const Color textPrimary = Color(0xFFFFFFFF);
  static const Color textSecondary = Color(0xFFB0B0B0);
  static const Color textTertiary = Color(0xFF888888);
  
  // UI Element Colors
  static const Color divider = Color(0xFF333333);
  static const Color cardBorder = Color(0xFF444444);
  static const Color ripple = Color(0x33FFFFFF);
  
  // Gradient Colors
  static final LinearGradient primaryGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [
      primaryBlue,
      accentCyan,
    ],
  );
  
  static final LinearGradient surfaceGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [
      surfaceDark,
      surfaceLight,
    ],
  );
}
