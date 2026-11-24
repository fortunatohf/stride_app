package expo.modules.strydelocation

import android.annotation.SuppressLint
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import android.os.Looper
import androidx.core.app.NotificationCompat
import com.google.android.gms.location.LocationCallback
import com.google.android.gms.location.LocationRequest
import com.google.android.gms.location.LocationResult
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import org.json.JSONObject
import java.io.File

/**
 * Foreground service that keeps GPS running while the screen is off. Android kills background apps,
 * but not a foreground service with a visible notification, which is what running apps rely on.
 */
class RunRecordingService : Service() {
  companion object {
    @Volatile var running = false
    private const val CHANNEL = "stryde_run"
    private const val NOTIF_ID = 4242
  }

  private val client by lazy { LocationServices.getFusedLocationProviderClient(this) }

  private val callback = object : LocationCallback() {
    override fun onLocationResult(result: LocationResult) {
      for (loc in result.locations) {
        val point = mapOf(
          "t" to loc.time.toDouble(),
          "lat" to loc.latitude,
          "lon" to loc.longitude,
          "alt" to if (loc.hasAltitude()) loc.altitude else null,
          "acc" to if (loc.hasAccuracy()) loc.accuracy.toDouble() else null,
          "speed" to if (loc.hasSpeed()) loc.speed.toDouble() else null,
        )
        RunBuffer.append(point)
      }
    }
  }

  override fun onBind(intent: Intent?): IBinder? = null

  @SuppressLint("MissingPermission")
  override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
    val title = intent?.getStringExtra("title") ?: "STRYDE is recording your run"
    val body = intent?.getStringExtra("body") ?: "Tap to return to your run"
    val interval = intent?.getLongExtra("intervalMs", 1000L) ?: 1000L
    RunBuffer.init(applicationContext)

    val notification = buildNotification(title, body)
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
      startForeground(NOTIF_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION)
    } else {
      startForeground(NOTIF_ID, notification)
    }

    val request = LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, interval)
      .setMinUpdateIntervalMillis(interval)
      .setMinUpdateDistanceMeters(0f)
      .setWaitForAccurateLocation(true)
      .build()
    try {
      client.requestLocationUpdates(request, callback, Looper.getMainLooper())
      running = true
    } catch (e: SecurityException) {
      RunBuffer.error("Location permission not granted")
      stopSelf()
    }
    return START_STICKY
  }

  override fun onDestroy() {
    client.removeLocationUpdates(callback)
    running = false
    super.onDestroy()
  }

  private fun buildNotification(title: String, body: String): Notification {
    val nm = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
      nm.createNotificationChannel(NotificationChannel(CHANNEL, "Run recording", NotificationManager.IMPORTANCE_LOW))
    }
    val launch = packageManager.getLaunchIntentForPackage(packageName)
    val pending = PendingIntent.getActivity(this, 0, launch, PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
    return NotificationCompat.Builder(this, CHANNEL)
      .setContentTitle(title)
      .setContentText(body)
      .setSmallIcon(android.R.drawable.ic_menu_mylocation)
      .setOngoing(true)
      .setContentIntent(pending)
      .build()
  }
}

/** Append-only JSONL buffer on disk + live listener to JS. */
object RunBuffer {
  private var file: File? = null
  var listener: ((Map<String, Any?>) -> Unit)? = null
  var errorListener: ((String) -> Unit)? = null

  fun init(ctx: Context) {
    if (file == null) file = File(ctx.filesDir, "stryde-run-buffer.jsonl")
  }

  @Synchronized fun append(point: Map<String, Any?>) {
    file?.appendText(JSONObject(point.mapValues { it.value ?: JSONObject.NULL }).toString() + "\n")
    listener?.invoke(point)
  }

  fun error(message: String) { errorListener?.invoke(message) }

  @Synchronized fun read(fromIndex: Int): List<Map<String, Any?>> {
    val f = file ?: return emptyList()
    if (!f.exists()) return emptyList()
    return f.readLines().drop(fromIndex).mapNotNull { line ->
      runCatching {
        val o = JSONObject(line)
        mapOf(
          "t" to o.getDouble("t"), "lat" to o.getDouble("lat"), "lon" to o.getDouble("lon"),
          "alt" to (if (o.isNull("alt")) null else o.getDouble("alt")),
          "acc" to (if (o.isNull("acc")) null else o.getDouble("acc")),
          "speed" to (if (o.isNull("speed")) null else o.getDouble("speed")),
        )
      }.getOrNull()
    }
  }

  @Synchronized fun clear() { file?.delete() }
}
