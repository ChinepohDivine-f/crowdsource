import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:jwt_decoder/jwt_decoder.dart';
import '../models/user.dart';

class AuthService with ChangeNotifier {
  // Base URL for production
  static const String baseUrl = 'https://crowdsource-backend-3ixx.onrender.com/api/v1/auth'; // PRODUCTION
  // static const String baseUrl = 'http://10.0.2.2:8000/api/v1/auth'; // LOCAL TESTING (Android Emulator)
  // static const String baseUrl = 'http://localhost:8000/api/v1/auth'; // LOCAL TESTING (iOS/Web/Physical)
  
  final _storage = const FlutterSecureStorage();
  String? _token;
  User? _currentUser;
  bool _isLoading = false;
  bool _isInitialized = false;
  String? _errorMessage;

  bool get isAuthenticated => _token != null && !JwtDecoder.isExpired(_token!);
  User? get currentUser => _currentUser;
  bool get isLoading => _isLoading;
  bool get isInitialized => _isInitialized;
  String? get errorMessage => _errorMessage;
  String? get token => _token;

  Future<void> loadUser() async {
    try {
      _token = await _storage.read(key: 'jwt_token');
      if (_token != null) {
        if (JwtDecoder.isExpired(_token!)) {
          await logout();
        } else {
          await _fetchUserProfile();
        }
      }
    } catch (e) {
      debugPrint("Initialization error: $e");
    } finally {
      _isInitialized = true;
      notifyListeners();
    }
  }

  Future<void> _fetchUserProfile() async {
    if (_token == null) return;
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/me'),
        headers: {'Authorization': 'Bearer $_token'},
      );

      if (response.statusCode == 200) {
        _currentUser = User.fromJson(jsonDecode(response.body));
        notifyListeners();
      } else {
        await logout();
      }
    } catch (e) {
      debugPrint("Error fetching user profile: $e");
    }
  }

  Future<bool> login(String email, String password) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      debugPrint("Attempting login for: $email");
      final response = await http.post(
          Uri.parse('$baseUrl/token'),
          headers: {'Content-Type': 'application/x-www-form-urlencoded'},
          body: {'username': email, 'password': password},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _token = data['access_token'];
        await _storage.write(key: 'jwt_token', value: _token);
        await _fetchUserProfile();
        debugPrint("Login success for: $email");
        _isLoading = false;
        notifyListeners();
        return true;
      } else {
        final errorBody = jsonDecode(response.body);
        _errorMessage = errorBody['detail'] ?? "Unauthorized access denied";
        debugPrint("Login failed [${response.statusCode}]: $_errorMessage");
        _isLoading = false;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _errorMessage = "Network error. Please check your connection.";
      debugPrint("Login network error: $e");
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<bool> register(String email, String username, String password) async {
    _isLoading = true;
    notifyListeners();

    try {
      final response = await http.post(
        Uri.parse('$baseUrl/register'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': email, 
          'username': username,
          'password': password
        }),
      );

      _isLoading = false;
      notifyListeners();
      return response.statusCode == 200;
    } catch (e) {
      print("Registration error: $e");
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<void> logout() async {
    _token = null;
    _currentUser = null;
    await _storage.delete(key: 'jwt_token');
    notifyListeners();
  }
}
