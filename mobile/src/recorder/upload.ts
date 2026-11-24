import * as Device from 'expo-device';

import { api } from '../api/client';
import { getPoints, pendingUploads, setStatus } from './store';

/** Upload one finished run. The run id doubles as an idempotency key, so retries never create duplicates. */
export async function uploadRun(runId: string): Promise<number> {
  const pts = getPoints(runId);
  const res = await api<{ id: number }>('/api/activities/', {
    body: {
      client_id: runId,
      device: Device.modelName ?? 'phone',
      points: pts.map((p) => ({ t: new Date(p.t).toISOString(), lat: p.lat, lon: p.lon, alt: p.alt, acc: p.acc })),
    },
  });
  setStatus(runId, 'uploaded', res.id);
  return res.id;
}

/** Retry runs that finished offline. Call on app start and when the app returns to the foreground. */
export async function flushPendingUploads() {
  for (const run of pendingUploads()) {
    try {
      await uploadRun(run.id);
    } catch {
      break; // still offline or server down; try again later
    }
  }
}
