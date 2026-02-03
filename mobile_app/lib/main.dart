import 'package:flutter/material.dart';
import 'screens/dashboard_page.dart';

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
      title: 'Crowdsensed Drive Test',
      theme: ThemeData(
        brightness: Brightness.dark, // Premium dark theme as requested
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: const DashboardPage(),
    );
  }
}
