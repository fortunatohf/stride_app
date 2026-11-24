package expo.modules.strydelocation

import android.content.Intent
import android.os.Build
import androidx.core.content.ContextCompat
import expo.modules.kotlin.modules.Module
import expo.modules.kotlin.modules.ModuleDefinition
import expo.modules.kotlin.records.Field
import expo.modules.kotlin.records.Record

class StartOptions : Record {
  @Field val intervalMs: Long = 1000
  @Field val notificationTitle: String = "STRYDE is recording your run"
  @Field val notificationBody: String = "Tap to return to your run"
}

class StrydeLocationModule : Module() {
  override fun definition() = ModuleDefinition {
    Name("StrydeLocation")
    Events("onLocation", "onError")

    OnCreate {
      RunBuffer.init(appContext.reactContext!!.applicationContext)
      RunBuffer.listener = { point -> sendEvent("onLocation", point) }
      RunBuffer.errorListener = { message -> sendEvent("onError", mapOf("message" to message)) }
    }

    OnDestroy {
      RunBuffer.listener = null
      RunBuffer.errorListener = null
    }

    AsyncFunction("start") { options: StartOptions ->
      val ctx = appContext.reactContext ?: throw IllegalStateException("No context")
      val intent = Intent(ctx, RunRecordingService::class.java).apply {
        putExtra("intervalMs", options.intervalMs)
        putExtra("title", options.notificationTitle)
        putExtra("body", options.notificationBody)
      }
      if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
        ContextCompat.startForegroundService(ctx, intent)
      } else {
        ctx.startService(intent)
      }
    }

    AsyncFunction("stop") {
      val ctx = appContext.reactContext ?: return@AsyncFunction
      ctx.stopService(Intent(ctx, RunRecordingService::class.java))
    }

    Function("isRecording") { RunRecordingService.running }

    AsyncFunction("getBufferedPoints") { fromIndex: Int -> RunBuffer.read(fromIndex) }

    AsyncFunction("clearBuffer") { RunBuffer.clear() }
  }
}
