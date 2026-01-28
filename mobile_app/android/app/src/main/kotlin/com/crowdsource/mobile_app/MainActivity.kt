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
                    val info = getRadioInfo()
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

    private fun getRadioInfo(): Map<String, Any>? {
        val telephonyManager = getSystemService(Context.TELEPHONY_SERVICE) as TelephonyManager
        val cellInfoList = telephonyManager.allCellInfo ?: return null
        
        for (cellInfo in cellInfoList) {
            if (cellInfo.isRegistered) {
                val data = mutableMapOf<String, Any>()
                if (cellInfo is CellInfoLte) {
                    val ss = cellInfo.cellSignalStrength
                    val identity = cellInfo.cellIdentity
                    data["type"] = "4G"
                    data["rsrp"] = ss.rsrp
                    data["rsrq"] = ss.rsrq
                    data["sinr"] = ss.rssnr
                    data["cellId"] = identity.ci.toLong()
                    return data
                } else if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q && cellInfo is CellInfoNr) {
                    data["type"] = "5G"
                    val ss = cellInfo.cellSignalStrength as CellSignalStrengthNr
                    val identity = cellInfo.cellIdentity as CellIdentityNr
                    data["rsrp"] = ss.ssRsrp
                    data["rsrq"] = ss.ssRsrq
                    data["sinr"] = ss.ssSinr
                    data["cellId"] = identity.nci
                    return data
                }
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
