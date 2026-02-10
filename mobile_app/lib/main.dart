import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'screens/splash_screen.dart';
import 'screens/login_screen.dart';
import 'screens/dashboard_page.dart';
import 'services/auth_service.dart';
import 'theme/app_theme.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthService()..loadUser()),
      ],
      child: const CrowdsourceApp(),
    ),
  );
}

class CrowdsourceApp extends StatelessWidget {
  const CrowdsourceApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Senzor - Network Intelligence',
      theme: AppTheme.darkTheme,
      home: const AuthWrapper(),
    );
  }
}

class AuthWrapper extends StatefulWidget {
  const AuthWrapper({super.key});

  @override
  _AuthWrapperState createState() => _AuthWrapperState();
}

class _AuthWrapperState extends State<AuthWrapper> {
  @override
  void initState() {
    super.initState();
    // Simulate splash delay or wait for auth load
    Future.delayed(const Duration(seconds: 2), () {});
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AuthService>(
      builder: (context, auth, _) {
        if (auth.isLoading) {
           return const SplashScreen(); // Or a loading spinner
        }
        return auth.isAuthenticated ? const DashboardPage() : const LoginScreen();
      },
    );
  }
}
