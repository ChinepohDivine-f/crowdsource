import 'package:flutter/material.dart';
import '../theme/app_colors.dart';
import '../theme/app_theme.dart';

class HelpPage extends StatelessWidget {
  const HelpPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Help & Documentation'),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(AppTheme.spacingM),
          children: [
            Text(
              'Welcome to Senzor! 👋',
              style: Theme.of(context).textTheme.displayMedium,
            ),
            const SizedBox(height: AppTheme.spacingS),
            Text(
              'Your personal network intelligence tool for contributing to crowdsourced coverage mapping.',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: AppTheme.spacingXL),
            
            _buildSection(
              context,
              icon: Icons.rocket_launch,
              title: 'Getting Started',
              children: [
                _buildStep(context, '1', 'Ensure Location & Phone permissions are granted'),
                _buildStep(context, '2', 'Enable mobile data (LTE or 5G)'),
                _buildStep(context, '3', 'Tap "Start Measurement" on the dashboard'),
                _buildStep(context, '4', 'Move around to collect data points'),
                _buildStep(context, '5', 'Tap "Stop" when finished'),
                _buildStep(context, '6', 'Tap "Sync Data" to upload to the server'),
              ],
            ),
            
            _buildSection(
              context,
              icon: Icons.analytics,
              title: 'Understanding Network Metrics',
              children: [
                _buildMetricCard(
                  context,
                  'RSRP',
                  'Reference Signal Received Power',
                  'Measures signal strength. Higher is better.\n• Excellent: > -80 dBm\n• Good: -80 to -100 dBm\n• Fair: -100 to -110 dBm\n• Poor: < -110 dBm',
                ),
                _buildMetricCard(
                  context,
                  'RSRQ',
                  'Reference Signal Received Quality',
                  'Measures signal quality (interference).\n• Excellent: > -10 dB\n• Good: -10 to -15 dB\n• Fair: -15 to -20 dB\n• Poor: < -20 dB',
                ),
                _buildMetricCard(
                  context,
                  'SINR',
                  'Signal to Interference & Noise Ratio',
                  'How clear the signal is vs. noise.\n• Excellent: > 20 dB\n• Good: 13 to 20 dB\n• Fair: 0 to 13 dB\n• Poor: < 0 dB',
                ),
                _buildMetricCard(
                  context,
                  'Cell ID',
                  'Cell Tower Identifier',
                  'Unique identifier of the cell tower you are connected to. Helps identify specific coverage areas.',
                ),
              ],
            ),
            
            _buildSection(
              context,
              icon: Icons.cloud_upload,
              title: 'Data Synchronization',
              children: [
                _buildInfoCard(
                  context,
                  'When does data sync?',
                  'Data is stored locally on your device until you manually tap "Sync Data". This ensures you don\'t lose measurements if you\'re offline.',
                ),
                _buildInfoCard(
                  context,
                  'How much data is uploaded?',
                  'Each measurement is very small (~100 bytes). Even 1000 measurements use less than 100KB of mobile data.',
                ),
                _buildInfoCard(
                  context,
                  'What happens after sync?',
                  'Your data is analyzed by our backend to detect coverage holes, generate heatmaps, and predict signal strength using machine learning.',
                ),
              ],
            ),
            
            _buildSection(
              context,
              icon: Icons.help_outline,
              title: 'Troubleshooting',
              children: [
                _buildFAQ(
                  context,
                  'Why is my RSRP showing "-140"?',
                  'This usually means your phone cannot read the signal strength. Make sure:\n• You have mobile data enabled\n• You are not in Airplane mode\n• Your SIM card is active',
                ),
                _buildFAQ(
                  context,
                  'Sync failed, what to do?',
                  'Check:\n• Internet connection (WiFi or mobile data)\n• Backend server URL is correct in settings\n• Try again in a few seconds (server may be sleeping on free tier)',
                ),
                _buildFAQ(
                  context,
                  'App crashes when I start measuring',
               'Make sure you\'ve granted Location and Phone permissions in your device settings.',
                ),
                _buildFAQ(
                  context,
                  'How do I see my contribution?',
                  'Visit the backend web dashboard at the URL shown in the app settings. You can view analytics, heatmaps, and ML predictions!',
                ),
              ],
            ),
            
            const SizedBox(height: AppTheme.spacingXL),
            _buildFooter(context),
          ],
        ),
      ),
    );
  }

  Widget _buildSection(
    BuildContext context, {
    required IconData icon,
    required String title,
    required List<Widget> children,
  }) {
    return Card(
      margin: const EdgeInsets.only(bottom: AppTheme.spacingM),
      child: ExpansionTile(
        leading: Icon(icon, color: AppColors.primaryBlue, size: 28),
        title: Text(
          title,
          style: Theme.of(context).textTheme.headlineSmall,
        ),
        initiallyExpanded: true,
        children: children,
      ),
    );
  }

  Widget _buildStep(BuildContext context, String number, String text) {
    return Padding(
      padding: const EdgeInsets.symmetric(
        vertical: AppTheme.spacingS,
        horizontal: AppTheme.spacingM,
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              color: AppColors.primaryBlue,
              shape: BoxShape.circle,
            ),
            child: Center(
              child: Text(
                number,
                style: const TextStyle(
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
            ),
          ),
          const SizedBox(width: AppTheme.spacingM),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.only(top: 6),
              child: Text(
                text,
                style: Theme.of(context).textTheme.bodyLarge,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricCard(
    BuildContext context,
    String abbr,
    String full,
    String description,
  ) {
    return Card(
      margin: const EdgeInsets.symmetric(
        vertical: AppTheme.spacingS,
        horizontal: AppTheme.spacingM,
      ),
      child: Padding(
        padding: const EdgeInsets.all(AppTheme.spacingM),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: AppTheme.spacingM,
                    vertical: AppTheme.spacingS,
                  ),
                  decoration: BoxDecoration(
                    color: AppColors.primaryBlue,
                    borderRadius: BorderRadius.circular(AppTheme.radiusS),
                  ),
                  child: Text(
                    abbr,
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 16,
                      color: Colors.white,
                    ),
                  ),
                ),
                const SizedBox(width: AppTheme.spacingM),
                Expanded(
                  child: Text(
                    full,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppTheme.spacingM),
            Text(
              description,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoCard(BuildContext context, String question, String answer) {
    return Card(
      margin: const EdgeInsets.symmetric(
        vertical: AppTheme.spacingS,
        horizontal: AppTheme.spacingM,
      ),
      color: AppColors.surfaceLight,
      child: Padding(
        padding: const EdgeInsets.all(AppTheme.spacingM),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.info_outline, color: AppColors.primaryBlue, size: 20),
                const SizedBox(width: AppTheme.spacingS),
                Expanded(
                  child: Text(
                    question,
                    style: Theme.of(context).textTheme.labelLarge,
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppTheme.spacingS),
            Text(
              answer,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFAQ(BuildContext context, String question, String answer) {
    return Card(
      margin: const EdgeInsets.symmetric(
        vertical: AppTheme.spacingS,
        horizontal: AppTheme.spacingM,
      ),
      child: ExpansionTile(
        tilePadding: const EdgeInsets.symmetric(
          horizontal: AppTheme.spacingM,
          vertical: AppTheme.spacingS,
        ),
        title: Text(
          question,
          style: Theme.of(context).textTheme.labelLarge,
        ),
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(
              AppTheme.spacingM,
              0,
              AppTheme.spacingM,
              AppTheme.spacingM,
            ),
            child: Text(
              answer,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFooter(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(AppTheme.spacingL),
      decoration: BoxDecoration(
        color: AppColors.surfaceLight,
        borderRadius: BorderRadius.circular(AppTheme.radiusM),
      ),
      child: Column(
        children: [
          Icon(Icons.favorite, color: AppColors.error, size: 32),
          const SizedBox(height: AppTheme.spacingM),
          Text(
            'Thank you for contributing to better network coverage!',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
          ),
          const SizedBox(height: AppTheme.spacingS),
          Text(
            'Every measurement helps map the real-world network experience.',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }
}
