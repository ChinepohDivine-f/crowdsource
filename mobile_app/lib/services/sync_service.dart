import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:connectivity_plus/connectivity_plus.dart';
import 'database_helper.dart';

class SyncService {
  final String apiUrl = "http://YOUR_LOCAL_IP:8000/measurements/"; // Update with host IP for real device

  Future<void> syncData() async {
    var connectivityResult = await (Connectivity().checkConnectivity());
    if (connectivityResult.contains(ConnectivityResult.none)) {
      return; 
    }

    final measurements = await DatabaseHelper.instance.queryAllMeasurements();
    if (measurements.isEmpty) return;

    try {
      final response = await http.post(
        Uri.parse(apiUrl),
        headers: {"Content-Type": "application/json"},
        body: json.encode(measurements.map((m) {
          // Prepare for API format
          var map = Map<String, dynamic>.from(m);
          map.remove('id'); // ID is local
          return map;
        }).toList()),
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        // Success! Clear local cache
        await DatabaseHelper.instance.clearAll();
        print("Synced ${measurements.length} records successfully.");
      } else {
        print("Failed to sync: ${response.statusCode}");
      }
    } catch (e) {
      print("Error during sync: $e");
    }
  }
}
