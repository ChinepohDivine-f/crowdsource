import 'package:flutter/material.dart';

/// HelpPage: Provides user documentation and data interpretation guides.
/// 
/// This screen is essential for fulfilling the assignment requirement of 
/// explaining the crowdsensing logic and metric significance to the user.
class HelpPage extends StatelessWidget {
  const HelpPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Help & Interpretation'),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildSectionTitle('📡 What is Crowdsensing?'),
              _buildContentText(
                'This app turns your mobile device into a network probe. By moving around, you help map cellular network performance in real-time. This "crowdsensed" data is used to identify where network upgrades are needed.',
              ),
              const Divider(height: 40),
              
              _buildSectionTitle('📊 Understanding Metrics'),
              _buildMetricItem(
                'RSRP (Signal Strength)',
                'Measures the power of the received signal. Higher is better.',
                [
                  'Excellent: > -80 dBm',
                  'Good: -80 to -90 dBm',
                  'Fair: -90 to -110 dBm',
                  'Poor (Hole): < -110 dBm (Red Marker)',
                ],
              ),
              const SizedBox(height: 20),
              _buildMetricItem(
                'SINR (Signal Quality)',
                'Measures the quality of the signal relative to noise. Higher is better.',
                [
                  'Excellent: > 20 dB',
                  'Good: 13 to 20 dB',
                  'Fair: 0 to 13 dB',
                  'Poor: < 0 dB',
                ],
              ),
              const SizedBox(height: 20),
              _buildMetricItem(
                'RSRQ (Signal Quality)',
                'Indicates the quality of the received signal. Higher is better.',
                [
                  'Excellent: > -10 dB',
                  'Good: -10 to -15 dB',
                  'Fair: -15 to -20 dB',
                  'Poor: < -20 dB',
                ],
              ),
              const SizedBox(height: 20),
              _buildMetricItem(
                'RSSI (Total Received Power)',
                'Total power received by the antenna. Typically used for 4G/LTE.',
                [
                  'Excellent: > -65 dBm',
                  'Good: -65 to -75 dBm',
                  'Fair: -75 to -85 dBm',
                  'Poor: < -85 dBm',
                ],
              ),
              const Divider(height: 40),
              
              _buildSectionTitle('📍 Map Interpretation'),
              _buildContentText(
                '• Green Markers: Indicate good coverage (RSRP > -110 dBm).\n'
                '• Red Markers: Indicate "Coverage Holes" where signal strength is critically low.\n'
                '• Current Location: The map centers on your position during collection.',
              ),
              const Divider(height: 40),

              _buildSectionTitle('⚙️ How to use'),
              _buildContentText(
                '1. Tap START COLLECTION to begin tracking.\n'
                '2. Data is saved locally every 10 seconds.\n'
                '3. Use the SYNC button (top right dashboard) to upload data to the central database when online.',
              ),
              const Divider(height: 40),

              _buildSectionTitle('📶 Collection Modes'),
              _buildMetricItem(
                'Provider Mode (Recommended)',
                'Standard mode for drive testing.',
                [
                  'Requires an active SIM card.',
                  'Only records data when the device is registered with a carrier.',
                  'Prevents "ghost" readings by stopping when signal is officially lost.',
                ],
              ),
              const SizedBox(height: 20),
              _buildMetricItem(
                'Raw Mode (Advanced)',
                'Capture ambient signal without a SIM.',
                [
                  'Bypasses SIM checks.',
                  'Records signal info from any visible tower (like SOS mode).',
                  'Useful for identifying ambient coverage when no service is active.',
                ],
              ),
              const Divider(height: 40),

              _buildSectionTitle('🌐 Web Dashboard'),
              _buildContentText(
                'Once your data is synced, you can view the global heatmap and analytics on the web interface. This dashboard features an interactive map where you can filter results by device name and timestamp.',
              ),
              const Divider(height: 40),

              _buildSectionTitle('❓ Troubleshooting & Rules of Thumb'),
              _buildMetricItem(
                'No Signal Recorded?',
                'If you see missing data or "N/A":',
                [
                  'Location Off: Ensure GPS is enabled. Without location, we cannot tag the signal.',
                  'Permissions: Verify the app has "Always Allow" or "While Using" location access.',
                ],
              ),
              const SizedBox(height: 20),
              _buildMetricItem(
                'No SIM Card / Airplane Mode',
                'The app requires an active cellular connection to measure signal.',
                [
                  'No SIM: Value will be 0, -1, or N/A. We cannot measure a network that isn\'t there.',
                  'Airplane Mode: All radios are off. No data will be collected, and the app may show "N/A".',
                ],
              ),
              const SizedBox(height: 20),
              _buildMetricItem(
                'Best Practices',
                'For the best drive test results:',
                [
                  'Speed: Drive at a steady moderate speed (e.g., 30-50 km/h) for accurate sampling.',
                  'Mounting: Place phone on dashboard for clear GPS view.',
                  'Screen: Keep the app open (screen on) to ensure uninterrupted collection.',
                ],
              ),
              const SizedBox(height: 20),
              _buildMetricItem(
                'Good Rules of Thumb (RF)',
                'Typical target values for a healthy network:',
                [
                  'RSRP > -90 dBm (Strong signal)',
                  'SINR > 13 dB (Low interference)',
                  'RSRQ > -12 dB (Reliable quality)',
                  'RSSI > -70 dBm (High total power)',
                ],
              ),
              const SizedBox(height: 40),
              
              Center(
                child: Text(
                  'v1.0.0 - Crowdsensed Project',
                  style: TextStyle(color: Colors.white.withOpacity(0.5)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  /// Helper to build consistent section titles
  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Text(
        title,
        style: const TextStyle(
          fontSize: 22,
          fontWeight: FontWeight.bold,
          color: Colors.blueAccent,
        ),
      ),
    );
  }

  /// Helper to build consistent body text
  Widget _buildContentText(String text) {
    return Text(
      text,
      style: const TextStyle(fontSize: 16, height: 1.5),
    );
  }

  /// Helper to build metric descriptions with ranges
  Widget _buildMetricItem(String title, String description, List<String> ranges) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 4),
        Text(description, style: const TextStyle(fontSize: 14, color: Colors.grey)),
        const SizedBox(height: 8),
        ...ranges.map((range) => Padding(
              padding: const EdgeInsets.only(left: 8, bottom: 4),
              child: Text('• $range', style: const TextStyle(fontSize: 14)),
            )),
      ],
    );
  }
}
