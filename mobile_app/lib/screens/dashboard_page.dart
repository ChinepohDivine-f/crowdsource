import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart' as ll;
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';
import '../services/telephony_service.dart';
import '../services/location_service.dart';
import '../services/database_helper.dart';
import '../services/sync_service.dart';
import 'help_page.dart';
import 'profile_screen.dart';
import '../theme/app_colors.dart';

/// DashboardPage: The main interface for network data collection and visualization.
class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> with SingleTickerProviderStateMixin {
  final TelephonyService _telephony = TelephonyService();
  final LocationService _location = LocationService();
  final SyncService _sync = SyncService();

  bool _isCollecting = false;
  bool _isRawMode = false;
  bool _isSyncing = false;
  int _pendingMeasurements = 0;
  String _displayName = "Loading..."; // Changed from _deviceName shorthand
  Timer? _timer;
  Map<String, dynamic>? _currentInfo;
  ll.LatLng? _currentPosition;
  
  final List<Marker> _markers = [];
  final MapController _mapController = MapController();
  late AnimationController _fadeController;

  @override
  void initState() {
    super.initState();
    _updatePendingCount();
    _fadeController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
      value: 1.0,
    );
    
    // Load User Profile for display name
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final auth = Provider.of<AuthService>(context, listen: false);
      setState(() {
         if (auth.currentUser?.username != null && auth.currentUser!.username!.isNotEmpty) {
           _displayName = auth.currentUser!.username!;
         } else {
           _displayName = auth.currentUser?.email ?? "Unknown User";
         }
      });
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    _fadeController.dispose();
    super.dispose();
  }

  Future<void> _updatePendingCount() async {
    final measurements = await DatabaseHelper.instance.queryAllMeasurements();
    setState(() {
      _pendingMeasurements = measurements.length;
    });
  }

  void _toggleCollection() {
    setState(() {
      _isCollecting = !_isCollecting;
      if (_isCollecting) {
        _timer = Timer.periodic(const Duration(seconds: 2), (timer) {
          _collectData();
        });
      } else {
        _timer?.cancel();
      }
    });
  }

  Future<void> _collectData() async {
    try {
      final pos = await _location.getCurrentLocation();
      final radio = await _telephony.getRadioInfo(rawMode: _isRawMode);
      final now = DateTime.now();

      if (pos != null && radio != null) {
        // Safe access now that we checked for null
        final rsrp = radio['rsrp'] as int? ?? -140;
        final status = _getSignalStatus(rsrp); 

        final measurement = {
          'device_id': _displayName,
          'network_type': radio['type'],
          'rsrp': rsrp,
          'rsrq': radio['rsrq'],
          'rssi': radio['rssi'],
          'sinr': radio['sinr'],
          'cell_id': radio['cellId'],
          'status': status,
          'latitude': pos.latitude,
          'longitude': pos.longitude,
          'timestamp': DateFormat('yyyy-MM-ddTHH:mm:ss').format(now),
        };

        await DatabaseHelper.instance.insertMeasurement(measurement);
        await _updatePendingCount();
        
        final newPos = ll.LatLng(pos.latitude, pos.longitude);
        final newMarker = _createMarker(
          pos.latitude, 
          pos.longitude, 
          rsrp,
          radio['rsrq'],
          radio['rssi'],
          radio['sinr'],
          radio['type'],
        );

        setState(() {
          _currentInfo = radio;
          _currentPosition = newPos;
          _markers.add(newMarker);
        });
        
        _moveMap(newPos);
      } else {
        // Handle null cases if needed
      }
    } catch (e) {
      debugPrint("Error collecting data: $e");
    }
  }

  String _getSignalStatus(int rsrp) {
    if (rsrp > -90) return 'Excellent';
    if (rsrp > -105) return 'Good';
    if (rsrp > -115) return 'Fair';
    return 'Poor';
  }

  Color _getSignalColor(int rsrp) {
    if (rsrp > -90) return Colors.green; // Excellent
    if (rsrp > -105) return Colors.lightGreen; // Good
    if (rsrp > -115) return Colors.yellow; // Fair
    return Colors.red; // Poor/Hole
  }

  Marker _createMarker(double lat, double lon, int rsrp, [int? rsrq, int? rssi, int? sinr, String? type]) {
    final color = _getSignalColor(rsrp);
    final timeStr = DateFormat('HH:mm:ss').format(DateTime.now());

    return Marker(
      point: ll.LatLng(lat, lon),
      width: 40,
      height: 40,
      child: GestureDetector(
        onTap: () {
          showDialog(
            context: context,
            builder: (context) => AlertDialog(
              backgroundColor: AppColors.surfaceDark,
              title: const Text('Signal Details', style: TextStyle(color: Colors.white)),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildDetailRow('Time', timeStr),
                  _buildDetailRow('Network', type ?? 'Unknown'),
                  _buildDetailRow('RSRP', '$rsrp dBm', valueColor: color),
                  _buildDetailRow('RSRQ', '${rsrq ?? "N/A"} dB'),
                  _buildDetailRow('RSSI', '${rssi ?? "N/A"} dBm'),
                  _buildDetailRow('SINR', '${sinr ?? "N/A"} dB'),
                  _buildDetailRow('Quality', _getSignalStatus(rsrp), valueColor: color),
                  _buildDetailRow('Location', '${lat.toStringAsFixed(4)}, ${lon.toStringAsFixed(4)}'),
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
          Icons.location_pin,
          size: 40,
          color: color,
          shadows: [
            Shadow(blurRadius: 2, color: Colors.black.withOpacity(0.5), offset: const Offset(1, 1))
          ],
        ),
      ),
    );
  }

  Widget _buildDetailRow(String label, String value, {Color? valueColor}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: AppColors.textSecondary)),
          Text(value, style: TextStyle(color: valueColor ?? Colors.white, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  void _moveMap(ll.LatLng position) {
    try {
      _mapController.move(position, 16.0);
    } catch (e) {
      debugPrint("MapController not ready yet: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundDark,
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: Colors.transparent, 
        elevation: 0,
        centerTitle: true,
        title: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          decoration: BoxDecoration(
            color: AppColors.surfaceDark.withOpacity(0.9),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: AppColors.cardBorder.withOpacity(0.5)),
          ),
          child: const Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.radar, color: AppColors.primaryBlue, size: 20),
              SizedBox(width: 8),
              Text('SENZOR', style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 1.2)),
            ],
          ),
        ),
        actions: [
           _buildAppBarIconButton(
            icon: Icons.person_outline, 
            tooltip: 'Profile',
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (c) => const ProfileScreen()))
          ),
          Stack(
            children: [
              _buildAppBarIconButton(
                icon: _isSyncing ? Icons.sync : Icons.cloud_upload_outlined,
                tooltip: 'Sync Data',
                onPressed: _isSyncing ? null : _handleSync,
                isLoading: _isSyncing,
              ),
              if (_pendingMeasurements > 0 && !_isSyncing)
                Positioned(
                  right: 8,
                  top: 8,
                  child: Container(
                    padding: const EdgeInsets.all(4),
                    decoration: const BoxDecoration(
                      color: AppColors.accentCyan,
                      shape: BoxShape.circle,
                    ),
                    constraints: const BoxConstraints(minWidth: 12, minHeight: 12),
                  ),
                ),
            ],
          ),
          const SizedBox(width: 8),
        ],
      ),
      drawer: _buildDrawer(),
      body: Stack(
        children: [
          // Map Layer - Using standard OSM for better visibility as requested
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: const ll.LatLng(9.0820, 8.6753),
              initialZoom: 6,
            ),
            children: [
              TileLayer(
                // Replacing dark map with a lighter, high-contrast one or standard OSM
                urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png', 
                userAgentPackageName: 'com.crowdsource.mobile_app',
              ),
              MarkerLayer(markers: _markers),
            ],
          ),

          // Map Control Buttons (Zoom, Reset)
          Positioned(
            right: 16,
            bottom: 260,
            child: Column(
              children: [
                _buildMapControlBtn(Icons.my_location, () async {
                   final pos = await _location.getCurrentLocation();
                   if (pos != null) _moveMap(ll.LatLng(pos.latitude, pos.longitude));
                }),
                const SizedBox(height: 12),
                _buildMapControlBtn(Icons.delete_outline, _showResetConfirmation, isDestructive: true),
              ],
            ),
          ),

          // Floating Network Type Badge (Top Right)
          if (_currentInfo != null)
            Positioned(
              top: 100, // Below AppBar
              right: 16,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: _getSignalColor(_currentInfo!['rsrp'] ?? -140),
                  borderRadius: BorderRadius.circular(30),
                  boxShadow: [
                    BoxShadow(color: Colors.black.withOpacity(0.3), blurRadius: 8, offset: const Offset(0, 4)),
                  ],
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.network_cell, color: Colors.white, size: 20),
                    const SizedBox(width: 8),
                    Text(
                      _currentInfo!['type'] ?? 'Unknown',
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                  ],
                ),
              ),
            ),

          // Horizontal Metrics Scroll View (Bottom)
          Align(
            alignment: Alignment.bottomCenter,
            child: Container(
              height: 140, // Height for scroll view
              margin: const EdgeInsets.only(bottom: 20),
              child: ListView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                children: [
                   _buildFloatingMetricCard('RSRP', '${_currentInfo?['rsrp'] ?? '-'}', 'dBm', _getSignalColor(_currentInfo?['rsrp'] ?? -140)),
                   _buildFloatingMetricCard('RSRQ', '${_currentInfo?['rsrq'] ?? '-'}', 'dB', Colors.blueGrey),
                   _buildFloatingMetricCard('SINR', '${_currentInfo?['sinr'] ?? '-'}', 'dB', Colors.teal),
                   _buildFloatingMetricCard('RSSI', '${_currentInfo?['rssi'] ?? '-'}', 'dBm', Colors.orange),
                   _buildFloatingMetricCard('CID', '${_currentInfo?['cellId'] ?? '-'}', '', Colors.purple),
                   
                   // Start/Stop Button as a Card at the end
                   Container(
                     margin: const EdgeInsets.only(right: 12, bottom: 8, top: 8),
                     width: 100,
                     child: ElevatedButton(
                        onPressed: _toggleCollection,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: _isCollecting ? Colors.red : AppColors.primaryBlue,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                          elevation: 6,
                        ),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(_isCollecting ? Icons.stop : Icons.play_arrow, size: 32),
                            const SizedBox(height: 4),
                            Text(_isCollecting ? 'STOP' : 'START', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                          ],
                        ),
                     ),
                   ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFloatingMetricCard(String label, String value, String unit, Color color) {
    return Container(
      width: 100,
      margin: const EdgeInsets.only(right: 12, bottom: 8, top: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.surfaceDark.withOpacity(0.9),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withOpacity(0.5), width: 2),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.3), blurRadius: 6, offset: const Offset(0, 4)),
        ],
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(label, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Text(value, style: TextStyle(color: color, fontSize: 20, fontWeight: FontWeight.bold)),
          if (unit.isNotEmpty)
             Text(unit, style: const TextStyle(color: AppColors.textTertiary, fontSize: 10)),
        ],
      ),
    );
  }

  // Helper method removed (replaced by direct usage in build)
  // Widget _buildLegendItem...

  
  // Drawer to house extra options like "Change Name" and "Help" to declutter UI
  Widget _buildDrawer() {
    return Drawer(
      backgroundColor: AppColors.backgroundDark,
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          DrawerHeader(
            decoration: BoxDecoration(
              gradient: AppColors.primaryGradient,
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                const Icon(Icons.radar, color: Colors.white, size: 48),
                const SizedBox(height: 16),
                const Text('Senzor', style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold)),
                Text(_displayName, style: const TextStyle(color: Colors.white70, fontSize: 14)),
              ],
            ),
          ),
          ListTile(
            leading: const Icon(Icons.edit, color: AppColors.textSecondary),
            title: const Text('Change Device Name', style: TextStyle(color: Colors.white)),
            onTap: () {
              Navigator.pop(context);
              _showChangeNameDialog();
            },
          ),
          ListTile(
            leading: const Icon(Icons.help_outline, color: AppColors.textSecondary),
            title: const Text('Help & Documentation', style: TextStyle(color: Colors.white)),
            onTap: () {
              Navigator.pop(context);
              Navigator.push(context, MaterialPageRoute(builder: (context) => const HelpPage()));
            },
          ),
          SwitchListTile(
            title: const Text('Raw Mode (No SIM)', style: TextStyle(color: Colors.white)),
            subtitle: const Text('Collect ambient signals', style: TextStyle(color: AppColors.textTertiary, fontSize: 12)),
            secondary: const Icon(Icons.developer_mode, color: AppColors.textSecondary),
            value: _isRawMode,
            onChanged: (val) => setState(() => _isRawMode = val),
            activeColor: AppColors.primaryBlue,
          ),
        ],
      ),
    );
  }

  Future<void> _showChangeNameDialog() async {
    String? newName = await showDialog<String>(
      context: context,
      builder: (context) {
        String input = _displayName;
        return AlertDialog(
          backgroundColor: AppColors.surfaceDark,
          title: const Text('Change Device Name', style: TextStyle(color: Colors.white)),
          content: TextField(
            autofocus: true,
            style: const TextStyle(color: Colors.white),
            decoration: InputDecoration(
              hintText: 'Enter new phone name',
              hintStyle: const TextStyle(color: AppColors.textTertiary),
              enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: AppColors.cardBorder)),
              focusedBorder: OutlineInputBorder(borderSide: BorderSide(color: AppColors.primaryBlue)),
            ),
            onChanged: (val) => input = val,
            controller: TextEditingController(text: _displayName),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel', style: TextStyle(color: AppColors.textSecondary)),
            ),
            ElevatedButton(
              onPressed: () => Navigator.pop(context, input),
              style: ElevatedButton.styleFrom(backgroundColor: AppColors.primaryBlue),
              child: const Text('Save'),
            ),
          ],
        );
      },
    );

    if (newName != null && newName.trim().isNotEmpty) {
      setState(() {
        _displayName = newName.trim();
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Device name changed to: $_displayName')),
        );
      }
    }
  }

  Future<void> _handleSync() async {
    setState(() => _isSyncing = true);
    
    // Haptic feedback could be added here
    
    try {
      final success = await _sync.syncData();
      if (mounted) {
        if (success) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('✅ Sync successful!'), backgroundColor: AppColors.success),
          );
          await _updatePendingCount();
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('❌ Sync failed! Check connection.'), backgroundColor: AppColors.error),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
           SnackBar(content: Text('Sync error: $e'), backgroundColor: AppColors.error),
        );
      }
    } finally {
      if (mounted) setState(() => _isSyncing = false);
    }
  }

  Future<void> _showResetConfirmation() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.surfaceDark,
        title: const Text('Reset Application?', style: TextStyle(color: Colors.white)),
        content: const Text(
          'This will stop data collection, clear all markers from the map, and PERMANENTLY delete all unsynced data.',
          style: TextStyle(color: AppColors.textSecondary),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('CANCEL', style: TextStyle(color: AppColors.textSecondary)),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.error),
            child: const Text('RESET EVERYTHING', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      _resetEverything();
    }
  }

  Widget _buildAppBarIconButton({
    required IconData icon, 
    required String tooltip, 
    required VoidCallback? onPressed,
    bool isLoading = false
  }) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 4),
      decoration: BoxDecoration(
        color: AppColors.surfaceDark.withOpacity(0.6),
        shape: BoxShape.circle,
        border: Border.all(color: AppColors.cardBorder.withOpacity(0.3)),
      ),
      child: IconButton(
        icon: isLoading 
          ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
          : Icon(icon, color: Colors.white, size: 20),
        tooltip: tooltip,
        onPressed: onPressed,
      ),
    );
  }

  Widget _buildMapControlBtn(IconData icon, VoidCallback onTap, {bool isDestructive = false}) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.surfaceDark.withOpacity(0.9),
        shape: BoxShape.circle,
        border: Border.all(color: AppColors.cardBorder.withOpacity(0.5)),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.3), blurRadius: 8),
        ],
      ),
      child: IconButton(
        icon: Icon(icon, color: isDestructive ? AppColors.error : Colors.white),
        onPressed: onTap,
      ),
    );
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
          backgroundColor: AppColors.success,
        ),
      );
    }
  }
}
