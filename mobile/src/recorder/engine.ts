import * as Location from 'expo-location';
import * as TaskManager from 'expo-task-manager';

import { StrydeLocation, type NativePoint } from '../../modules/stryde-location';
import { activeRun, addPoints, getNativeIndex, setNativeIndex, type StoredPoint } from './store';

/**
 * Two recording engines behind one interface:
 * - native: modules/stryde-location (Core Location / Android foreground service). Used in dev and store builds.
 * - expo:   expo-location background task. Fallback (e.g. Expo Go, where only foreground works on iOS).
 */
export const LOCATION_TASK = 'stryde-run-location';

type Listener = (p: StoredPoint) => void;
const listeners = new Set<Listener>();
let nativeSub: { remove(): void } | null = null;

const toStored = (p: NativePoint): StoredPoint => ({ t: p.t, lat: p.lat, lon: p.lon, alt: p.alt, acc: p.acc, speed: p.speed });

// Must be defined at module scope so it is registered before any background wake-up.
TaskManager.defineTask<{ locations: Location.LocationObject[] }>(LOCATION_TASK, async ({ data, error }) => {
  if (error || !data) return;
  const run = activeRun();
  if (!run) return;
  const pts: StoredPoint[] = data.locations.map((l) => ({
    t: l.timestamp,
    lat: l.coords.latitude,
    lon: l.coords.longitude,
    alt: l.coords.altitude ?? null,
    acc: l.coords.accuracy ?? null,
    speed: l.coords.speed ?? null,
  }));
  addPoints(run.id, pts);
  pts.forEach((p) => listeners.forEach((fn) => fn(p)));
});

export const engineName = () => (StrydeLocation ? 'native' : 'expo');

export async function ensurePermissions(): Promise<{ ok: boolean; background: boolean }> {
  const fg = await Location.requestForegroundPermissionsAsync();
  if (fg.status !== 'granted') return { ok: false, background: false };
  // Background ("Always") lets the run continue with the screen locked. Ask only when starting a run.
  const bg = await Location.requestBackgroundPermissionsAsync().catch(() => ({ status: 'denied' as const }));
  return { ok: true, background: bg.status === 'granted' };
}

function attachNative(runId: string) {
  if (!StrydeLocation) return;
  nativeSub?.remove();
  nativeSub = StrydeLocation.addListener('onLocation', (p) => {
    const sp = toStored(p);
    addPoints(runId, [sp]);
    listeners.forEach((fn) => fn(sp));
  });
}

/** After a JS reload mid-run, reconnect to the native recorder that kept running. */
export function reattachEngine(runId: string) {
  if (StrydeLocation?.isRecording()) attachNative(runId);
}

export async function startEngine(runId: string) {
  if (StrydeLocation) {
    attachNative(runId);
    await StrydeLocation.clearBuffer();
    setNativeIndex(runId, 0);
    await StrydeLocation.start({
      intervalMs: 1000,
      notificationTitle: 'STRYDE is recording your run',
      notificationBody: 'Tap to return to your run',
    });
    return;
  }
  await Location.startLocationUpdatesAsync(LOCATION_TASK, {
    accuracy: Location.Accuracy.BestForNavigation,
    timeInterval: 1000,
    distanceInterval: 0,
    activityType: Location.ActivityType.Fitness,
    pausesUpdatesAutomatically: false,
    showsBackgroundLocationIndicator: true,
    foregroundService: { notificationTitle: 'STRYDE is recording your run', notificationBody: 'Tap to return to your run', notificationColor: '#D7FF3A' },
  });
}

/** Pull any points the native recorder buffered while JS was paused or reloaded. */
export async function syncNativeBuffer(runId: string) {
  if (!StrydeLocation) return;
  const from = getNativeIndex(runId);
  const pts = await StrydeLocation.getBufferedPoints(from);
  if (pts.length) {
    addPoints(runId, pts.map(toStored));
    setNativeIndex(runId, from + pts.length);
  }
}

export async function stopEngine(runId: string) {
  if (StrydeLocation) {
    await syncNativeBuffer(runId);
    await StrydeLocation.stop();
    nativeSub?.remove();
    nativeSub = null;
    return;
  }
  if (await Location.hasStartedLocationUpdatesAsync(LOCATION_TASK)) {
    await Location.stopLocationUpdatesAsync(LOCATION_TASK);
  }
}

export function onPoint(fn: Listener) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}
