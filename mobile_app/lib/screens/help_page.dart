import 'package:flutter/material.dart';
import '../theme/app_colors.dart';
import '../theme/app_theme.dart';

class HelpPage extends StatelessWidget {
  const HelpPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundDark,
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        title: const Text('Help & Documentation'),
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        iconTheme: const IconThemeData(color: Colors.white),
        titleTextStyle: const TextStyle(
          color: Colors.white, 
          fontSize: 20, 
          fontWeight: FontWeight.bold
        ),
      ),
      body: Stack(
        children: [
          // Background Elements
          Positioned(
            top: -150,
            right: -100,
            child: _buildBlurCircle(200, AppColors.primaryBlue.withOpacity(0.1)),
          ),
          Positioned(
            bottom: -50,
            left: -50,
            child: _buildBlurCircle(150, AppColors.accentCyan.withOpacity(0.1)),
          ),

          SafeArea(
            child: ListView(
              padding: const EdgeInsets.all(AppTheme.spacingM),
              children: [
                _buildHeader(context),
                const SizedBox(height: AppTheme.spacingXL),
                
                _buildSection(
                  context,
                  icon: Icons.rocket_launch,
                  title: 'Getting Started',
                  children: [
                    _buildStep(context, '1', 'Ensure Location & Phone permissions are granted'),
                    _buildStep(context, '2', 'Enable mobile data (LTE or 5G)'),
                    _buildStep(context, '3', 'Tap "Start Monitoring" on the dashboard'),
                    _buildStep(context, '4', 'Move around to collect data points'),
                    _buildStep(context, '5', 'Tap "Stop Collection" when finished'),
                    _buildStep(context, '6', 'Tap "Sync Data" to upload to the server'),
                  ],
                ),
                
                _buildSection(
                  context,
                  icon: Icons.analytics,
                  title: 'Network Metrics',
                  children: [
                    _buildMetricCard(
                      context,
                      'RSRP',
                      'ref_signal',
                      'Signal Strength',
                      'Measures signal power. Higher is better.\n• Excellent: > -80 dBm\n• Good: -80 to -100 dBm\n• Fair: -100 to -110 dBm\n• Poor (Hole): < -110 dBm',
                      AppColors.primaryBlue,
                    ),
                    _buildMetricCard(
                      context,
                      'SINR',
                      'interference',
                      'Signal Quality',
                      'Signal vs Noise ratio. Higher is better.\n• Excellent: > 20 dB\n• Good: 13 to 20 dB\n• Fair: 0 to 13 dB\n• Poor: < 0 dB',
                      AppColors.accentCyan,
                    ),
                    _buildMetricCard(
                      context,
                      'RSRQ',
                      'quality',
                      'Received Quality',
                      'Overall channel quality.\n• Excellent: > -10 dB\n• Good: -10 to -15 dB\n• Fair: -15 to -20 dB\n• Poor: < -20 dB',
                      Colors.purpleAccent,
                    ),
                  ],
                ),
                
                _buildSection(
                  context,
                  icon: Icons.cloud_sync,
                  title: 'Data Synchronization',
                  children: [
                    _buildInfoCard(
                      context,
                      'Storage',
                      'Data is stored securely on your device until synced.',
                      Icons.sd_storage,
                    ),
                    _buildInfoCard(
                      context,
                      'Bandwidth',
                      'Syncing is optimized. 1000 points < 100KB.',
                      Icons.data_usage,
                    ),
                    _buildInfoCard(
                      context,
                      'Analysis',
                      'Uploaded data helps identify coverage holes globally.',
                      Icons.public,
                    ),
                  ],
                ),
                
                _buildSection(
                  context,
                  icon: Icons.help_outline,
                  title: 'FAQ',
                  children: [
                    _buildFAQ(
                      context,
                      'Why is RSRP "-140"?',
                      'Phone cannot detect signal. Check SIM status or Airplane mode.',
                    ),
                    _buildFAQ(
                      context,
                      'Sync Failed?',
                      'Check internet connection. Server might be sleeping (free tier).',
                    ),
                    _buildFAQ(
                      context,
                      'App Crashes?',
                      'Ensure all permissions (Location, Phone) are granted in settings.',
                    ),
                  ],
                ),
                
                const SizedBox(height: AppTheme.spacingXL),
                _buildFooter(context),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Column(
      children: [
        const Icon(Icons.help_center_outlined, size: 60, color: AppColors.accentCyan),
        const SizedBox(height: 16),
        Text(
          'Welcome to Senzor',
          style: Theme.of(context).textTheme.headlineMedium?.copyWith(
            color: Colors.white,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'Crowdsourced Network Intelligence',
          style: Theme.of(context).textTheme.bodyLarge?.copyWith(
            color: AppColors.textSecondary,
          ),
        ),
      ],
    );
  }

  Widget _buildSection(
    BuildContext context, {
    required IconData icon,
    required String title,
    required List<Widget> children,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 24),
      decoration: BoxDecoration(
        color: AppColors.surfaceDark.withOpacity(0.6),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.cardBorder.withOpacity(0.5)),
      ),
      child: Theme(
        data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
        child: ExpansionTile(
          leading: Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: AppColors.primaryBlue.withOpacity(0.1),
              shape: BoxShape.circle,
            ),
            child: Icon(icon, color: AppColors.primaryBlue, size: 24),
          ),
          title: Text(
            title,
            style: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.bold,
              fontSize: 18,
            ),
          ),
          childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
          initiallyExpanded: title == 'Getting Started',
          iconColor: Colors.white70,
          collapsedIconColor: Colors.white70,
          children: children,
        ),
      ),
    );
  }

  Widget _buildStep(BuildContext context, String number, String text) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 28,
            height: 28,
            alignment: Alignment.center,
            decoration: const BoxDecoration(
              color: AppColors.accentCyan,
              shape: BoxShape.circle,
            ),
            child: Text(
              number,
              style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white),
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(color: AppColors.textSecondary, height: 1.4),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricCard(
    BuildContext context,
    String abbr,
    String subtitle,
    String fullTitle,
    String description,
    Color color,
  ) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surfaceLight.withOpacity(0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.cardBorder.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  abbr,
                  style: TextStyle(
                    color: color,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Text(
                fullTitle,
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            description,
            style: const TextStyle(color: AppColors.textSecondary, fontSize: 13, height: 1.5),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoCard(BuildContext context, String title, String description, IconData icon) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surfaceLight.withOpacity(0.05),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Icon(icon, color: AppColors.textTertiary, size: 24),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                const SizedBox(height: 4),
                Text(description, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFAQ(BuildContext context, String question, String answer) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(question, style: const TextStyle(color: AppColors.accentCyan, fontWeight: FontWeight.w600)),
          const SizedBox(height: 4),
          Text(answer, style: const TextStyle(color: AppColors.textSecondary, fontSize: 13)),
        ],
      ),
    );
  }

  Widget _buildFooter(BuildContext context) {
    return Column(
      children: [
        const Icon(Icons.favorite, color: AppColors.error, size: 24),
        const SizedBox(height: 12),
        const Text(
          'Mapping the world, one signal at a time.',
          style: TextStyle(color: AppColors.textTertiary, fontStyle: FontStyle.italic),
        ),
        const SizedBox(height: 40),
      ],
    );
  }
  
  Widget _buildBlurCircle(double radius, Color color) {
    return Container(
      width: radius * 2,
      height: radius * 2,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: color,
        boxShadow: [
          BoxShadow(
            color: color,
            blurRadius: 50,
            spreadRadius: 20,
          ),
        ],
      ),
    );
  }
}
