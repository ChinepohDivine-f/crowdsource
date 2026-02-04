import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:device_info_plus/device_info_plus.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:io';
import 'database_helper.dart';

class SyncService {
  // Base URL - ensure this matches your backend IP
  // final String baseUrl = "http://172.18.232.209:8000/api/v1";
  final String baseUrl = "https://crowdsource-backend-3ixx.onrender.com/api/v1";

  Future<String?> _getStoredToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('api_key');
  }

  Future<void> _saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('api_key', token);
  }

  Future<String?> _registerDevice() async {
    try {
      DeviceInfoPlugin deviceInfo = DeviceInfoPlugin();
      String manufacturer = "Unknown";
      String model = "Unknown";
      String osVersion = "Unknown";
      String deviceId = "Unknown";

      if (Platform.isAndroid) {
        AndroidDeviceInfo androidInfo = await deviceInfo.androidInfo;
        manufacturer = androidInfo.manufacturer;
        model = androidInfo.model;
        osVersion = "Android ${androidInfo.version.release} (SDK ${androidInfo.version.sdkInt})";
        deviceId = androidInfo.id; // Unique ID on Android
      }

      final payload = {
        "device_id": deviceId,
        "manufacturer": manufacturer,
        "model": model,
        "os_version": osVersion
      };

      debugPrint("🔐 Registering Device: $deviceId");

      final response = await http.post(
        Uri.parse("$baseUrl/register"),
        headers: {"Content-Type": "application/json"},
        body: json.encode(payload),
      ).timeout(const Duration(seconds: 15));

      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        String token = body['api_key'];
        debugPrint("✅ Registration Successful. Token received.");
        await _saveToken(token);
        return token;
      } else {
        debugPrint("❌ Registration Failed: ${response.statusCode} - ${response.body}");
        return null;
      }
    } catch (e) {
      debugPrint("🧨 Registration Error: $e");
      return null;
    }
  }

  Future<bool> syncData() async {
    // 1. Check Connectivity
    var connectivityResult = await (Connectivity().checkConnectivity());
    if (connectivityResult.contains(ConnectivityResult.none)) {
      debugPrint("⚠️ No Internet Connection. Skipping Sync.");
      return false; 
    }

    // 2. Authentication Check
    String? token = await _getStoredToken();
    if (token == null) {
      debugPrint("🚫 No API Token found. Attempting registration...");
      token = await _registerDevice();
      if (token == null) {
        debugPrint("❌ Aborting Sync: Could not authenticate device.");
        return false;
      }
    }

    // 3. Fetch Pending Data
    final measurements = await DatabaseHelper.instance.queryAllMeasurements();
    if (measurements.isEmpty) return true; 

    try {
      // 4. Construct Payload
      // We need device_id again for metadata, normally we'd cache this too, but for MVp let's re-fetch or use placeholder
      // Ideally registration should store profile too.
      // Let's grab basic info again lightly.
      DeviceInfoPlugin deviceInfo = DeviceInfoPlugin();
      String deviceId = "Unknown";
      if (Platform.isAndroid) {
        AndroidDeviceInfo androidInfo = await deviceInfo.androidInfo;
        deviceId = androidInfo.id; 
      }

      final batchData = measurements.map((m) {
        int ts = 0;
        try {
          ts = DateTime.parse(m['timestamp']).millisecondsSinceEpoch ~/ 1000;
        } catch (e) {
          ts = DateTime.now().millisecondsSinceEpoch ~/ 1000;
        }

        return {
          "ts": ts,
          "lat": m['latitude'] ?? 0.0,
          "lon": m['longitude'] ?? 0.0,
          "acc": 10.0,
          "net": m['network_type'] ?? "UNKNOWN",
          "mcc": 0, "mnc": 0, "ci": m['cell_id'] ?? 0,
          "metrics": {
            "rsrp": m['rsrp'] ?? -140,
            "rsrq": m['rsrq'], "rssi": m['rssi'], "sinr": m['sinr']
          }
        };
      }).toList();

      final payload = {
        "meta": {
          "device_id": deviceId,
          "batch_size": batchData.length,
          "client_timestamp": DateTime.now().millisecondsSinceEpoch ~/ 1000,
          // Minimal meta needed as we are auth'd
        },
        "data": batchData
      };

      // 5. Send Authenticated Request
      final response = await http.post(
        Uri.parse("$baseUrl/ingest/batch"),
        headers: {
          "Content-Type": "application/json",
          "Authorization": "Token $token"
        },
        body: json.encode(payload),
      ).timeout(const Duration(seconds: 30));

      // 6. Handle Response
      if (response.statusCode == 200 || response.statusCode == 201) {
        await DatabaseHelper.instance.clearAll();
        debugPrint("✅ Sync Success: ${batchData.length} records uploaded.");
        return true;
      } else if (response.statusCode == 401 || response.statusCode == 403) {
        debugPrint("⛔ Auth Error during sync (Token expired?). Clearing token.");
        final prefs = await SharedPreferences.getInstance();
        await prefs.remove('api_key');
        return false;
      } else {
        debugPrint("❌ Sync Failed! Status: ${response.statusCode}");
        return false;
      }
    } catch (e) {
      debugPrint("🧨 Sync Error: $e");
      return false;
    }
  }
}
