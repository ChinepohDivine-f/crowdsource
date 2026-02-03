import 'package:flutter/services.dart';

class TelephonyService {
  static const MethodChannel _channel = MethodChannel('com.crowdsource/telephony');

  Future<Map<String, dynamic>?> getRadioInfo({bool rawMode = false}) async {
    try {
      final Map<dynamic, dynamic>? result = await _channel.invokeMethod(
        'getRadioInfo',
        {'rawMode': rawMode},
      );
      if (result != null) {
        return Map<String, dynamic>.from(result);
      }
    } on PlatformException catch (e) {
      print("Failed to get radio info: '${e.message}'.");
    }
    return null;
  }

  Future<String> getNetworkType() async {
    try {
      final String? result = await _channel.invokeMethod('getNetworkType');
      return result ?? "UNKNOWN";
    } on PlatformException catch (e) {
      print("Failed to get network type: '${e.message}'.");
      return "ERROR";
    }
  }
}
