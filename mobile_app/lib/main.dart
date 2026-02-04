import 'package:flutter/material.dart';
import 'screens/splash_screen.dart';
import 'theme/app_theme.dart';

/// Entry point of the Crowdsensing Application.
/// 
/// This file is now cleaner, serving as the app orchestrator while 
/// specialized logic resides in the 'screens' and 'services' directories.
void main() {
  runApp(const CrowdsourceApp());
}

class CrowdsourceApp extends StatelessWidget {
  const CrowdsourceApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Senzor - Network Intelligence',
      theme: AppTheme.darkTheme,
      home: const SplashScreen(),
    );
  }
}
