package com.crowdsource.mobile_app

import android.content.Context
import android.os.Build
import android.telephony.*
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    private val CHANNEL = "com.crowdsource/telephony"

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL).setMethodCallHandler { call, result ->
            when (call.method) {
                "getRadioInfo" -> {
                    val rawMode = call.argument<Boolean>("rawMode") ?: false
                    val info = getRadioInfo(rawMode)
                    if (info != null) {
                        result.success(info)
                    } else {
                        result.error("UNAVAILABLE", "Radio info not available.", null)
                    }
                }
                "getNetworkType" -> {
                    result.success(getNetworkType())
                }
                else -> {
                    result.notImplemented()
                }
            }
        }
    }

    private fun isAirplaneModeOn(): Boolean {
        return android.provider.Settings.Global.getInt(
            contentResolver,
            android.provider.Settings.Global.AIRPLANE_MODE_ON, 0
        ) != 0
    }

    private fun isSimReady(): Boolean {
        val telephonyManager = getSystemService(Context.TELEPHONY_SERVICE) as TelephonyManager
        return telephonyManager.simState == TelephonyManager.SIM_STATE_READY
    }

    private fun getRadioInfo(rawMode: Boolean): Map<String, Any>? {
        // Airplane mode usually kills the radio hardware. 
        // We only bypass SIM checks in Raw Mode.
        if (!rawMode && isAirplaneModeOn()) return null
        if (!rawMode && !isSimReady()) return null

        val telephonyManager = getSystemService(Context.TELEPHONY_SERVICE) as TelephonyManager
        val cellInfoList = telephonyManager.allCellInfo ?: return null
        
        // In Provider Mode, we only want 'isRegistered' cells.
        // In Raw Mode, we take any valid cell info, prioritizing registered ones.
        var bestCell: CellInfo? = cellInfoList.find { it.isRegistered }
        
        if (bestCell == null && rawMode && cellInfoList.isNotEmpty()) {
            bestCell = cellInfoList.firstOrNull() // Take the first available tower
        }

        if (bestCell != null) {
            val data = mutableMapOf<String, Any>()
            if (bestCell is CellInfoLte) {
                val ss = bestCell.cellSignalStrength
                val identity = bestCell.cellIdentity
                
                if (ss.rsrp == 2147483647) return null // Truly unavailable

                data["type"] = "4G"
                data["rsrp"] = ss.rsrp
                data["rsrq"] = ss.rsrq
                data["sinr"] = ss.rssnr
                data["cellId"] = if (identity.ci != 2147483647) identity.ci.toLong() else -1L
                
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                    data["rssi"] = if (ss.rssi != 2147483647) ss.rssi else -1
                } else {
                    data["rssi"] = -1
                }
                return data
            } else if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q && bestCell is CellInfoNr) {
                val ss = bestCell.cellSignalStrength as CellSignalStrengthNr
                val identity = bestCell.cellIdentity as CellIdentityNr
                
                if (ss.ssRsrp == 2147483647) return null

                data["type"] = "5G"
                data["rsrp"] = ss.ssRsrp
                data["rsrq"] = ss.ssRsrq
                data["sinr"] = ss.ssSinr
                data["rssi"] = -1
                data["cellId"] = if (identity.nci != 9223372036854775807L) identity.nci else -1L
                return data
            }
        }
        return null
    }

    private fun getNetworkType(): String {
        val telephonyManager = getSystemService(Context.TELEPHONY_SERVICE) as TelephonyManager
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            val type = telephonyManager.dataNetworkType
            return when (type) {
                TelephonyManager.NETWORK_TYPE_LTE -> "4G"
                20 -> "5G" // TelephonyManager.NETWORK_TYPE_NR is 20
                else -> "OTHER"
            }
        }
        return "OTHER"
    }
}
