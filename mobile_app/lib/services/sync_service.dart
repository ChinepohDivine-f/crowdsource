import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:device_info_plus/device_info_plus.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'dart:io';
import 'database_helper.dart';

class SyncService {
  // Base URL - ensure this matches your backend IP
  final String baseUrl = "https://crowdsource-backend-3ixx.onrender.com/api/v1";

  // Use SecureStorage to retrieve JWT
  final _storage = const FlutterSecureStorage();

  Future<String?> _getStoredToken() async {
    return await _storage.read(key: 'jwt_token');
  }

  Future<bool> syncData() async {
    // 1. Check Connectivity
    var connectivityResult = await (Connectivity().checkConnectivity());
    if (connectivityResult.contains(ConnectivityResult.none)) {
      debugPrint("⚠️ No Internet Connection. Skipping Sync.");
      return false; 
    }

    // 2. Authentication Check (JWT)
    String? token = await _getStoredToken();
    if (token == null) {
      debugPrint("🚫 No JWT Token found. User must be logged in to sync.");
      return false;
    }

    // 3. Fetch Pending Data
    final measurements = await DatabaseHelper.instance.queryAllMeasurements();
    if (measurements.isEmpty) return true; 

    try {
      // 4. Construct Payload
      DeviceInfoPlugin deviceInfo = DeviceInfoPlugin();
      String deviceId = "Unknown";
      String model = "Unknown";
      String osVersion = "Unknown";
      
      if (Platform.isAndroid) {
        AndroidDeviceInfo androidInfo = await deviceInfo.androidInfo;
        deviceId = androidInfo.id; 
        model = androidInfo.model;
        osVersion = "Android ${androidInfo.version.release}";
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
          "model": model,
          "os_version": osVersion,
          "batch_size": batchData.length,
          "client_timestamp": DateTime.now().millisecondsSinceEpoch ~/ 1000,
        },
        "data": batchData
      };

      // 5. Send Authenticated Request (Bearer Token)
      final response = await http.post(
        Uri.parse("$baseUrl/ingest/batch"),
        headers: {
          "Content-Type": "application/json",
          "Authorization": "Bearer $token"
        },
        body: json.encode(payload),
      ).timeout(const Duration(seconds: 30));

      // 6. Handle Response
      if (response.statusCode == 200 || response.statusCode == 201) {
        await DatabaseHelper.instance.clearAll();
        debugPrint("✅ Sync Success: ${batchData.length} records uploaded.");
        return true;
      } else if (response.statusCode == 401 || response.statusCode == 403) {
        debugPrint("⛔ Auth Error during sync (Token expired?).");
        return false;
      } else {
        debugPrint("❌ Sync Failed! Status: ${response.statusCode} - ${response.body}");
        return false;
      }
    } catch (e, stack) {
      debugPrint("🧨 Sync Error: $e");
      debugPrint(stack.toString());
      if (e is SocketException) {
        debugPrint("📡 Network unreachable. Backend might be down or URL is incorrect.");
      }
      return false;
    }
  }
}
