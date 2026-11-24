import CoreLocation
import ExpoModulesCore

/// Native run recorder for iPhone.
/// - Core Location with fitness activity type, best accuracy, no automatic pausing.
/// - Keeps running with the screen locked (needs UIBackgroundModes "location" + "Always"/"When in use" during a run).
/// - Every fix is appended to a JSONL file in Application Support, so a crash or JS reload loses nothing.
public class StrydeLocationModule: Module {
  private let recorder = Recorder()

  public func definition() -> ModuleDefinition {
    Name("StrydeLocation")
    Events("onLocation", "onError")

    OnCreate {
      self.recorder.onPoint = { [weak self] point in self?.sendEvent("onLocation", point) }
      self.recorder.onError = { [weak self] message in self?.sendEvent("onError", ["message": message]) }
    }

    AsyncFunction("start") { (_: [String: Any]) in
      try await MainActor.run { try self.recorder.start() }
    }

    AsyncFunction("stop") {
      await MainActor.run { self.recorder.stop() }
    }

    Function("isRecording") { () -> Bool in
      self.recorder.isRecording
    }

    AsyncFunction("getBufferedPoints") { (fromIndex: Int) -> [[String: Any]] in
      self.recorder.readBuffer(from: fromIndex)
    }

    AsyncFunction("clearBuffer") {
      self.recorder.clearBuffer()
    }
  }
}

final class Recorder: NSObject, CLLocationManagerDelegate {
  private let manager = CLLocationManager()
  private let queue = DispatchQueue(label: "stryde.location.buffer")
  private(set) var isRecording = false
  var onPoint: (([String: Any]) -> Void)?
  var onError: ((String) -> Void)?

  private lazy var bufferURL: URL = {
    let dir = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
    try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
    return dir.appendingPathComponent("stryde-run-buffer.jsonl")
  }()

  override init() {
    super.init()
    manager.delegate = self
    manager.activityType = .fitness
    manager.desiredAccuracy = kCLLocationAccuracyBestForNavigation
    manager.distanceFilter = kCLDistanceFilterNone
    manager.pausesLocationUpdatesAutomatically = false
  }

  func start() throws {
    let status = manager.authorizationStatus
    guard status == .authorizedAlways || status == .authorizedWhenInUse else {
      throw NSError(domain: "StrydeLocation", code: 1, userInfo: [NSLocalizedDescriptionKey: "Location permission not granted"])
    }
    manager.allowsBackgroundLocationUpdates = true
    manager.showsBackgroundLocationIndicator = true
    isRecording = true
    manager.startUpdatingLocation()
  }

  func stop() {
    manager.stopUpdatingLocation()
    manager.allowsBackgroundLocationUpdates = false
    isRecording = false
  }

  func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
    for loc in locations where loc.horizontalAccuracy >= 0 {
      let point: [String: Any] = [
        "t": loc.timestamp.timeIntervalSince1970 * 1000,
        "lat": loc.coordinate.latitude,
        "lon": loc.coordinate.longitude,
        "alt": loc.verticalAccuracy >= 0 ? loc.altitude : NSNull(),
        "acc": loc.horizontalAccuracy,
        "speed": loc.speed >= 0 ? loc.speed : NSNull(),
      ]
      append(point)
      onPoint?(point)
    }
  }

  func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
    onError?(error.localizedDescription)
  }

  private func append(_ point: [String: Any]) {
    queue.async {
      guard let data = try? JSONSerialization.data(withJSONObject: point) else { return }
      var line = data
      line.append(0x0A)
      if let handle = try? FileHandle(forWritingTo: self.bufferURL) {
        handle.seekToEndOfFile()
        handle.write(line)
        try? handle.close()
      } else {
        try? line.write(to: self.bufferURL)
      }
    }
  }

  func readBuffer(from index: Int) -> [[String: Any]] {
    queue.sync {
      guard let text = try? String(contentsOf: bufferURL, encoding: .utf8) else { return [] }
      let lines = text.split(separator: "\n")
      guard index < lines.count else { return [] }
      return lines[index...].compactMap { line in
        (try? JSONSerialization.jsonObject(with: Data(line.utf8))) as? [String: Any]
      }
    }
  }

  func clearBuffer() {
    queue.sync { try? FileManager.default.removeItem(at: bufferURL) }
  }
}
