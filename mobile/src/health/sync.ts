/**
 * Watch runs through the phone's health store:
 * - iPhone: Apple Health (Apple Watch, plus Garmin/COROS/Polar/Suunto/Wahoo when their app syncs to Apple Health)
 * - Android: Health Connect (Wear OS, Galaxy Watch, Pixel Watch, and brands that sync into it)
 *
 * We read running workouts with a GPS route, convert them to the backend's health payload, and upload.
 * The backend validates them exactly like a phone run.
 */
import * as HK from '@kingstinct/react-native-healthkit';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';
import * as HC from 'react-native-health-connect';

import { api } from '../api/client';

export type HealthPayload = {
  workout: { id: string; start: string; end: string; activity: string; source_name?: string; device?: string; was_user_entered: boolean };
  route: { t: string; lat: number; lon: number; alt?: number | null; acc?: number | null }[];
  heart_rate: { t: string; bpm: number }[];
};

const LAST_SYNC = 'stryde.health.lastSync';
const DEFAULT_LOOKBACK_DAYS = 14;

export const healthPlatform = Platform.OS === 'ios' ? 'healthkit' : 'health_connect';
export const healthName = Platform.OS === 'ios' ? 'Apple Health' : 'Health Connect';

// ---------- Apple Health ----------
const HK_RUNNING = [HK.WorkoutActivityType.running, HK.WorkoutActivityType.walking, HK.WorkoutActivityType.hiking];

async function hkAuthorize(): Promise<boolean> {
  if (!HK.isHealthDataAvailable()) return false;
  return HK.requestAuthorization({
    toRead: ['HKWorkoutTypeIdentifier', 'HKWorkoutRouteTypeIdentifier', 'HKQuantityTypeIdentifierHeartRate'],
  });
}

async function hkWorkouts(since: Date): Promise<HealthPayload[]> {
  const workouts = await HK.queryWorkoutSamples({
    limit: 50,
    ascending: false,
    filter: { date: { startDate: since }, OR: HK_RUNNING.map((t) => ({ workoutActivityType: t })) },
  });
  const out: HealthPayload[] = [];
  for (const w of workouts) {
    const routes = await w.getWorkoutRoutes();
    const locations = routes.flatMap((r) => r.locations);
    if (locations.length < 10) continue; // treadmill or no GPS: can't count on a route
    const hr = await HK.queryQuantitySamples('HKQuantityTypeIdentifierHeartRate', {
      limit: 0,
      unit: 'count/min',
      filter: { date: { startDate: w.startDate, endDate: w.endDate } },
    });
    const meta = (w.metadata ?? {}) as Record<string, unknown>;
    out.push({
      workout: {
        id: w.uuid,
        start: w.startDate.toISOString(),
        end: w.endDate.toISOString(),
        activity: w.workoutActivityType === HK.WorkoutActivityType.running ? 'running' : 'walking',
        source_name: w.sourceRevision?.source?.name,
        device: w.device?.model ?? w.sourceRevision?.productType,
        was_user_entered: meta.HKWasUserEntered === true || meta.HKWasUserEntered === 1,
      },
      route: locations.map((l) => ({
        t: l.date.toISOString(),
        lat: l.latitude,
        lon: l.longitude,
        alt: l.altitude,
        acc: l.horizontalAccuracy,
      })),
      heart_rate: hr.map((s) => ({ t: s.startDate.toISOString(), bpm: Math.round(s.quantity) })),
    });
  }
  return out;
}

// ---------- Health Connect ----------
const HC_RUNNING = new Set([56 /* RUNNING */, 79 /* WALKING */, 37 /* HIKING */]);

async function hcAuthorize(): Promise<boolean> {
  const ok = await HC.initialize();
  if (!ok) return false;
  const granted = await HC.requestPermission([
    { accessType: 'read', recordType: 'ExerciseSession' },
    { accessType: 'read', recordType: 'HeartRate' },
  ]);
  return granted.some((p) => 'recordType' in p && p.recordType === 'ExerciseSession');
}

async function hcWorkouts(since: Date): Promise<HealthPayload[]> {
  const { records } = await HC.readRecords('ExerciseSession', {
    timeRangeFilter: { operator: 'after', startTime: since.toISOString() },
  });
  const out: HealthPayload[] = [];
  for (const s of records) {
    if (!HC_RUNNING.has(s.exerciseType)) continue;
    const id = s.metadata?.id ?? `${s.startTime}`;
    let route = s.exerciseRoute?.route ?? [];
    if (!route.length && s.metadata?.id) {
      // Routes from other apps need a one-time consent per session on Android 14+.
      route = await HC.requestExerciseRoute(s.metadata.id).catch(() => []);
    }
    if (route.length < 10) continue;
    const hr = await HC.readRecords('HeartRate', {
      timeRangeFilter: { operator: 'between', startTime: s.startTime, endTime: s.endTime },
    }).catch(() => ({ records: [] as { samples: { time: string; beatsPerMinute: number }[] }[] }));
    out.push({
      workout: {
        id,
        start: s.startTime,
        end: s.endTime,
        activity: s.exerciseType === 56 ? 'running' : 'walking',
        source_name: s.metadata?.dataOrigin,
        device: s.metadata?.device?.model,
        was_user_entered: s.metadata?.recordingMethod === 3, // RECORDING_METHOD_MANUAL_ENTRY
      },
      route: route.map((l) => ({ t: l.time, lat: l.latitude, lon: l.longitude, alt: l.altitude?.value ?? null, acc: l.horizontalAccuracy?.value ?? null })),
      heart_rate: hr.records.flatMap((r) => r.samples.map((x) => ({ t: x.time, bpm: Math.round(x.beatsPerMinute) }))),
    });
  }
  return out;
}

// ---------- shared ----------
export async function connectHealth(): Promise<boolean> {
  try {
    return Platform.OS === 'ios' ? await hkAuthorize() : await hcAuthorize();
  } catch {
    return false;
  }
}

/** Read new watch runs since the last sync and upload them. Returns how many were sent. */
export async function syncHealth(): Promise<number> {
  const last = await SecureStore.getItemAsync(LAST_SYNC);
  const since = last ? new Date(last) : new Date(Date.now() - DEFAULT_LOOKBACK_DAYS * 86_400_000);
  const started = new Date();
  const workouts = Platform.OS === 'ios' ? await hkWorkouts(since) : await hcWorkouts(since);
  for (let i = 0; i < workouts.length; i += 5) {
    await api('/api/activities/health/', { body: { platform: healthPlatform, workouts: workouts.slice(i, i + 5) } });
  }
  await SecureStore.setItemAsync(LAST_SYNC, started.toISOString());
  return workouts.length;
}
