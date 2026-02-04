import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart' as ll;
import 'package:intl/intl.dart';
import '../services/telephony_service.dart';
import '../services/location_service.dart';
import '../services/database_helper.dart';
import '../services/sync_service.dart';
import 'help_page.dart';
import '../theme/app_colors.dart';

/// DashboardPage: The main interface for network data collection and visualization.
/// 
/// CITENOTE: This page integrates location, telephony, and database services 
/// to fulfill the real-time crowdsensing requirements of the project.
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
  bool _isRawMode = false;
  bool _isSyncing = false;
  int _pendingMeasurements = 0;
  String _deviceName = "Driver_Phone";
  Timer? _timer;
  Map<String, dynamic>? _currentInfo;
  ll.LatLng? _currentPosition;
  
  // CITENOTE: List used for OSM markers (flutter_map requirement)
  final List<Marker> _markers = [];
  final MapController _mapController = MapController();

  @override
  void initState() {
    super.initState();
    _updatePendingCount();
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _updatePendingCount() async {
    final measurements = await DatabaseHelper.instance.queryAllMeasurements();
    setState(() {
      _pendingMeasurements = measurements.length;
    });
  }

  /// Starts or stops the background data collection timer.
  void _toggleCollection() {
    setState(() {
      _isCollecting = !_isCollecting;
      if (_isCollecting) {
        // CITENOTE: Data collected every 10 seconds as per project specs.
        _timer = Timer.periodic(const Duration(seconds: 10), (timer) => _collectData());
      } else {
        _timer?.cancel();
      }
    });
  }

  /// Orchestrates data capture from sensors and saves to local database.
  Future<void> _collectData() async {
    try {
      final pos = await _location.getCurrentLocation();
      final radio = await _telephony.getRadioInfo(rawMode: _isRawMode);

      if (pos != null && radio != null) {
        final now = DateTime.now();
        final rsrp = radio['rsrp'];
        final status = (rsrp != null && rsrp > -110) ? 'Good' : 'Hole';

        final measurement = {
          'device_id': _deviceName,
          'network_type': radio['type'],
          'rsrp': radio['rsrp'],
          'rsrq': radio['rsrq'],
          'rssi': radio['rssi'],
          'sinr': radio['sinr'],
          'cell_id': radio['cellId'],
          'status': status,
          'latitude': pos.latitude,
          'longitude': pos.longitude,
          'timestamp': DateFormat('yyyy-MM-ddTHH:mm:ss').format(now),
        };

        // CITENOTE: Persistent local storage ensures data isn't lost offline.
      await DatabaseHelper.instance.insertMeasurement(measurement);
      await _updatePendingCount();
      
      final newPos = ll.LatLng(pos.latitude, pos.longitude);
      final newMarker = _createMarker(
        pos.latitude, 
        pos.longitude, 
        radio['rsrp'],
        radio['rsrq'],
        radio['rssi'],
      );

      setState(() {
        _currentInfo = radio;
        _currentPosition = newPos;
        _markers.add(newMarker);
      });

      // Safely move map if controller is ready
      _moveMap(newPos);

      // CITENOTE: Attempt background synchronization with FastAPI backend.
      _sync.syncData();
    } else {
      setState(() {
        _currentInfo = null; // Clear UI info if connection is lost
      });
      if (mounted) {
        String missing = "";
        if (pos == null) missing += "Location ";
        if (radio == null) missing += "Radio/SIM ";
        debugPrint("Data collection skipped: Missing $missing");
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Collection skipped: Missing $missing'), backgroundColor: Colors.yellow.shade700, duration: const Duration(seconds: 1)),
        );
      }
    }
    } catch (e) {
      debugPrint("Error collecting data: $e");
      if (mounted && _isCollecting) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Collection error: $e'), backgroundColor: Colors.orange),
        );
      }
    }
  }

  /// Creates a color-coded marker based on signal strength.
  Marker _createMarker(double lat, double lon, int rsrp, [int? radioRsrq, int? radioRssi]) {
    final now = DateTime.now();
    final timeStr = DateFormat('HH:mm:ss').format(now);
    
    return Marker(
      point: ll.LatLng(lat, lon),
      width: 40,
      height: 40,
      child: GestureDetector(
        onTap: () {
          showDialog(
            context: context,
            builder: (context) => AlertDialog(
              title: const Text('Measurement Details'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Time: $timeStr'),
                  Text('RSRP: $rsrp dBm'),
                  Text('RSRQ: ${radioRsrq ?? "N/A"} dB'),
                  Text('RSSI: ${radioRssi ?? "N/A"} dBm'),
                  Text('Status: ${rsrp < -110 ? "Coverage Hole" : "Good Signal"}'),
                  Text('Lat: ${lat.toStringAsFixed(5)}'),
                  Text('Lon: ${lon.toStringAsFixed(5)}'),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Close'),
                ),
              ],
            ),
          );
        },
        child: Icon(
          Icons.location_on,
          size: 40,
          // CITENOTE: Threshold of -110 dBm used to identify coverage holes.
          color: rsrp < -110 ? Colors.red : Colors.green,
        ),
      ),
    );
  }

  /// Safely moves the map to a new position if the controller is ready.
  void _moveMap(ll.LatLng position) {
    try {
      _mapController.move(position, 15.0);
    } catch (e) {
      debugPrint("MapController not ready yet: $e");
    }
  }

  @Deprecated('Use _createMarker instead to avoid redundant setState')
  void _addMarker(double lat, double lon, int rsrp, [int? rsrq, int? rssi]) {
    final marker = _createMarker(lat, lon, rsrp, rsrq, rssi);
    setState(() {
      _markers.add(marker);
      _moveMap(ll.LatLng(lat, lon));
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar:AppBar(
        title: const Text('Senzor'),
        actions: [
          IconButton(
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (context) => const HelpPage()),
            ),
            icon: const Icon(Icons.help_outline),
            tooltip: 'Help & Interpretation',
          ),
          IconButton(
            onPressed: _showChangeNameDialog,
            icon: const Icon(Icons.edit),
            tooltip: 'Change Device Name',
          ),
          Stack(
            children: [
              IconButton(
                onPressed: _isSyncing ? null : _handleSync,
                icon: _isSyncing 
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Icon(Icons.sync),
                tooltip: 'Sync Data',
              ),
              if (_pendingMeasurements > 0 && !_isSyncing)
                Positioned(
                  right: 6,
                  top: 6,
                  child: Container(
                    padding: const EdgeInsets.all(4),
                    decoration: BoxDecoration(
                      color: AppColors.error,
                      shape: BoxShape.circle,
                    ),
                    constraints: const BoxConstraints(
                      minWidth: 16,
                      minHeight: 16,
                    ),
                    child: Text(
                      _pendingMeasurements > 99 ? '99+' : '$_pendingMeasurements',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                ),
            ],
          ),
          IconButton(
            onPressed: _showResetConfirmation,
            icon: const Icon(Icons.delete_outline),
            tooltip: 'Clear Map & Data',
            color: Colors.redAccent,
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              flex: 3,
              child: Stack(
                children: [
                  FlutterMap(
                    mapController: _mapController,
                    options: MapOptions(
                      initialCenter: const ll.LatLng(9.0820, 8.6753), // Regional focus
                      initialZoom: 6,
                    ),
                    children: [
                      TileLayer(
                        urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                        userAgentPackageName: 'com.crowdsource.mobile_app',
                      ),
                      MarkerLayer(markers: _markers),
                    ],
                  ),
                  
                  // Map Legend Overlay
                  Positioned(
                    top: 10,
                    right: 10,
                    child: Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: Colors.black.withOpacity(0.7),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          _buildLegendItem(Colors.green, 'Good Signal'),
                          const SizedBox(height: 4),
                          _buildLegendItem(Colors.red, 'Coverage Hole'),
                        ],
                      ),
                    ),
                  ),

                  // Active Collection Indicator
                  if (_isCollecting)
                    Positioned(
                      top: 10,
                      left: 10,
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                        decoration: BoxDecoration(
                          color: Colors.red.withOpacity(0.8),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Row(
                          children: [
                            const _PulseIndicator(),
                            const SizedBox(width: 5),
                            const Text(
                              'COLLECTING',
                              style: TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                                fontSize: 12,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                ],
              ),
            ),
            
            // Stats and Control Panel
            Container(
              decoration: BoxDecoration(
                color: Theme.of(context).cardColor,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.2),
                    blurRadius: 10,
                    offset: const Offset(0, -5),
                  ),
                ],
              ),
              padding: const EdgeInsets.all(16),
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    // Mode Toggle
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Text('Provider Mode', style: TextStyle(fontSize: 12)),
                        Switch(
                          value: _isRawMode,
                          onChanged: (val) => setState(() => _isRawMode = val),
                          activeColor: Colors.blueAccent,
                        ),
                        const Text('Raw Mode (No SIM)', style: TextStyle(fontSize: 12)),
                      ],
                    ),
                    const Divider(),
                    const SizedBox(height: 10),

                    // Horizontal scroll for stats to avoid screen overflow
                    SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                        children: [
                          _buildStatCard(
                            'Network', 
                            _currentInfo?['type'] ?? 'N/A',
                            Colors.white,
                          ),
                          const SizedBox(width: 24),
                          _buildStatCard(
                            'RSRP', 
                            '${_currentInfo?['rsrp'] ?? 'N/A'} dBm',
                            _getRSRPColor(_currentInfo?['rsrp']),
                          ),
                          const SizedBox(width: 24),
                          _buildStatCard(
                            'SINR', 
                            '${_currentInfo?['sinr'] ?? 'N/A'} dB',
                            _getSINRColor(_currentInfo?['sinr']),
                          ),
                          const SizedBox(width: 24),
                          _buildStatCard(
                            'RSRQ', 
                            '${_currentInfo?['rsrq'] ?? 'N/A'} dB',
                            _getRSRQColor(_currentInfo?['rsrq']),
                          ),
                          const SizedBox(width: 24),
                          _buildStatCard(
                            'RSSI', 
                            '${_currentInfo?['rssi'] ?? 'N/A'} dBm',
                            _getRSSIColor(_currentInfo?['rssi']),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),
                    
                    // Main Action Button
                    SizedBox(
                      width: double.infinity,
                      height: 50,
                      child: ElevatedButton(
                        onPressed: _toggleCollection,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: _isCollecting ? Colors.red.shade700 : Colors.green.shade700,
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                        child: Text(
                          _isCollecting ? 'STOP COLLECTION' : 'START COLLECTION',
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            )
          ],
        ),
      ),
    );
  }

  /// Helper to build stat summary cards
  Widget _buildStatCard(String label, String value, Color color) {
    return Column(
      children: [
        Text(label, style: const TextStyle(fontWeight: FontWeight.bold)),
        Text(
          value, 
          style: TextStyle(
            fontSize: 18, 
            color: color,
            fontWeight: color != Colors.white ? FontWeight.bold : FontWeight.normal,
          ),
        ),
      ],
    );
  }

  Widget _buildLegendItem(Color color, String label) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 8),
        Text(label, style: const TextStyle(color: Colors.white, fontSize: 12)),
      ],
    );
  }

  Color _getRSRPColor(dynamic value) {
    if (value == null) return Colors.white;
    int rsrp = value is int ? value : int.tryParse(value.toString()) ?? -120;
    if (rsrp > -80) return Colors.greenAccent;
    if (rsrp > -110) return Colors.yellowAccent;
    return Colors.redAccent;
  }

  Color _getSINRColor(dynamic value) {
    if (value == null) return Colors.white;
    int sinr = value is int ? value : int.tryParse(value.toString()) ?? -10;
    if (sinr > 13) return Colors.greenAccent;
    if (sinr > 0) return Colors.yellowAccent;
    return Colors.redAccent;
  }

  Color _getRSRQColor(dynamic value) {
    if (value == null) return Colors.white;
    int rsrq = value is int ? value : int.tryParse(value.toString()) ?? -20;
    if (rsrq > -10) return Colors.greenAccent;
    if (rsrq > -15) return Colors.yellowAccent;
    return Colors.redAccent;
  }

  Future<void> _showChangeNameDialog() async {
    String? newName = await showDialog<String>(
      context: context,
      builder: (context) {
        String input = _deviceName;
        return AlertDialog(
          title: const Text('Change Device Name'),
          content: TextField(
            autofocus: true,
            decoration: const InputDecoration(hintText: 'Enter new phone name'),
            onChanged: (val) => input = val,
            controller: TextEditingController(text: _deviceName),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
            ElevatedButton(
              onPressed: () => Navigator.pop(context, input),
              child: const Text('Save'),
            ),
          ],
        );
      },
    );

    if (newName != null && newName.trim().isNotEmpty) {
      setState(() {
        _deviceName = newName.trim();
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Device name changed to: $_deviceName')),
        );
      }
    }
  }

  Color _getRSSIColor(dynamic value) {
    if (value == null) return Colors.white;
    int rssi = value is int ? value : int.tryParse(value.toString()) ?? -100;
    if (rssi > -65) return Colors.greenAccent;
    if (rssi > -75) return Colors.yellowAccent;
    return Colors.redAccent;
  }

  Future<void> _handleSync() async {
    setState(() {
      _isSyncing = true;
    });
    
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Syncing data to cloud...'), duration: Duration(seconds: 1)),
    );
    try {
      final success = await _sync.syncData();
      if (mounted) {
        if (success) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('✅ Sync successful!'), backgroundColor: Colors.green),
          );
          await _updatePendingCount();
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('❌ Sync failed! Check connection or server.'), backgroundColor: Colors.red),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Sync failed: $e'), backgroundColor: Colors.red),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isSyncing = false;
        });
      }
    }
  }

  Future<void> _showResetConfirmation() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Reset Application?'),
        content: const Text(
          'This will stop data collection, clear all markers from the map, and PERMANENTLY delete all unsynced data from your local database. This action cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('CANCEL'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('RESET EVERYTHING', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      _resetEverything();
    }
  }

  Future<void> _resetEverything() async {
    setState(() {
      if (_isCollecting) _toggleCollection();
      _markers.clear();
      _currentInfo = null;
    });

    await DatabaseHelper.instance.clearAll();

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('App reset successful. Local data cleared.'),
          backgroundColor: Colors.green,
        ),
      );
    }
  }
}

class _PulseIndicator extends StatefulWidget {
  const _PulseIndicator();

  @override
  State<_PulseIndicator> createState() => _PulseIndicatorState();
}

class _PulseIndicatorState extends State<_PulseIndicator> with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 1),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _controller,
      child: Container(
        width: 8,
        height: 8,
        decoration: const BoxDecoration(color: Colors.white, shape: BoxShape.circle),
      ),
    );
  }
}
