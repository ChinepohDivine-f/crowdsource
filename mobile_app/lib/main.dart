import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:intl/intl.dart';
import 'services/telephony_service.dart';
import 'services/location_service.dart';
import 'services/database_helper.dart';
import 'services/sync_service.dart';

void main() {
  runApp(const CrowdsourceApp());
}

class CrowdsourceApp extends StatelessWidget {
  const CrowdsourceApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Crowdsensed Drive Test',
      theme: ThemeData(
        brightness: Brightness.dark,
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: const DashboardPage(),
    );
  }
}

class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  final TelephonyService _telephony = TelephonyService();
  final LocationService _location = LocationService();
  final SyncService _sync = SyncService();

  bool _isCollecting = false;
  Timer? _timer;
  Map<String, dynamic>? _currentInfo;
  LatLng? _currentPosition;
  final Set<Marker> _markers = {};
  GoogleMapController? _mapController;

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  void _toggleCollection() {
    setState(() {
      _isCollecting = !_isCollecting;
      if (_isCollecting) {
        _timer = Timer.periodic(const Duration(seconds: 10), (timer) => _collectData());
      } else {
        _timer?.cancel();
      }
    });
  }

  Future<void> _collectData() async {
    final pos = await _location.getCurrentLocation();
    final radio = await _telephony.getRadioInfo();

    if (pos != null && radio != null) {
      final now = DateTime.now();
      final measurement = {
        'device_id': 'phone_01', // Example ID
        'network_type': radio['type'],
        'rsrp': radio['rsrp'],
        'sinr': radio['sinr'],
        'cell_id': radio['cellId'],
        'latitude': pos.latitude,
        'longitude': pos.longitude,
        'timestamp': DateFormat('yyyy-MM-ddTHH:mm:ss').format(now),
      };

      await DatabaseHelper.instance.insertMeasurement(measurement);
      
      setState(() {
        _currentInfo = radio;
        _currentPosition = LatLng(pos.latitude, pos.longitude);
        _addMarker(pos.latitude, pos.longitude, radio['rsrp']);
      });

      // Try to sync
      _sync.syncData();
    }
  }

  void _addMarker(double lat, double lon, int rsrp) {
    final markerId = MarkerId(DateTime.now().millisecondsSinceEpoch.toString());
    final marker = Marker(
      markerId: markerId,
      position: LatLng(lat, lon),
      infoWindow: InfoWindow(title: 'RSRP: $rsrp dBm'),
      icon: BitmapDescriptor.defaultMarkerWithHue(
        rsrp < -110 ? BitmapDescriptor.hueRed : BitmapDescriptor.hueGreen,
      ),
    );

    setState(() {
      _markers.add(marker);
      if (_mapController != null && _currentPosition != null) {
        _mapController!.animateCamera(CameraUpdate.newLatLng(_currentPosition!));
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Crowdsensed Drive Test'),
        actions: [
          IconButton(
            onPressed: () => _sync.syncData(),
            icon: const Icon(Icons.sync),
          )
        ],
      ),
      body: Column(
        children: [
          Expanded(
            flex: 2,
            child: GoogleMap(
              initialCameraPosition: const CameraPosition(
                target: LatLng(0, 0),
                zoom: 2,
              ),
              onMapCreated: (controller) => _mapController = controller,
              markers: _markers,
            ),
          ),
          Container(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    _buildStatCard('Network', _currentInfo?['type'] ?? 'N/A'),
                    _buildStatCard('RSRP', '${_currentInfo?['rsrp'] ?? 'N/A'} dBm'),
                    _buildStatCard('SINR', '${_currentInfo?['sinr'] ?? 'N/A'} dB'),
                  ],
                ),
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _toggleCollection,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: _isCollecting ? Colors.red : Colors.green,
                      foregroundColor: Colors.white,
                    ),
                    child: Text(_isCollecting ? 'STOP COLLECTION' : 'START COLLECTION'),
                  ),
                ),
              ],
            ),
          )
        ],
      ),
    );
  }

  Widget _buildStatCard(String label, String value) {
    return Column(
      children: [
        Text(label, style: const TextStyle(fontWeight: FontWeight.bold)),
        Text(value, style: const TextStyle(fontSize: 18)),
      ],
    );
  }
}
