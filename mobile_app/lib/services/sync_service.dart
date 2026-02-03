import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:connectivity_plus/connectivity_plus.dart';
import 'database_helper.dart';

class SyncService {
  final String apiUrl = "http://172.18.232.209:8000/measurements/";

  Future<bool> syncData() async {
    var connectivityResult = await (Connectivity().checkConnectivity());
    if (connectivityResult.contains(ConnectivityResult.none)) {
      return false; 
    }

    final measurements = await DatabaseHelper.instance.queryAllMeasurements();
    if (measurements.isEmpty) return true; // Nothing to sync is a "success"

    try {
      final jsonBody = json.encode(measurements.map((m) {
        var map = Map<String, dynamic>.from(m);
        map.remove('id');
        return map;
      }).toList());

      debugPrint("📡 Syncing to: $apiUrl");
      debugPrint("📦 Payload: $jsonBody");

      final response = await http.post(
        Uri.parse(apiUrl),
        headers: {"Content-Type": "application/json"},
        body: jsonBody,
      ).timeout(const Duration(seconds: 15));

      if (response.statusCode == 200 || response.statusCode == 201) {
        await DatabaseHelper.instance.clearAll();
        debugPrint("✅ Sync Success!");
        return true;
      } else {
        debugPrint("❌ Sync Failed! Status: ${response.statusCode}");
        debugPrint("⚠️ Server Response: ${response.body}");
        return false;
      }
    } catch (e) {
      debugPrint("🧨 Sync Error: $e");
      return false;
    }
  }
}
