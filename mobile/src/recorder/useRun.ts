import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { AppState } from 'react-native';

import type { RouteDetail } from '../api/types';
import { checkpointProgress, liveDistance } from '../geo';
import { ensurePermissions, onPoint, reattachEngine, startEngine, stopEngine, syncNativeBuffer } from './engine';
import { activeRun, createRun, discardRun, getPoints, setStatus, type StoredPoint } from './store';
import { uploadRun } from './upload';

export type RunPhase = 'idle' | 'recording' | 'saving' | 'saved' | 'error';

/** Recording state for the Run screen. Works for free runs and conquest attempts (pass the route). */
export function useRun(route?: RouteDetail | null) {
  const [phase, setPhase] = useState<RunPhase>('idle');
  const [runId, setRunId] = useState<string | null>(null);
  const [points, setPoints] = useState<StoredPoint[]>([]);
  const [now, setNow] = useState(Date.now());
  const [error, setError] = useState<string | null>(null);
  const [activityId, setActivityId] = useState<number | null>(null);
  const startedAt = useRef<number | null>(null);

  // Resume a run that was still recording when the app was closed or reloaded.
  useEffect(() => {
    const run = activeRun();
    if (run) {
      setRunId(run.id);
      startedAt.current = run.started_at;
      reattachEngine(run.id);
      syncNativeBuffer(run.id).then(() => setPoints(getPoints(run.id)));
      setPhase('recording');
    }
  }, []);

  useEffect(() => {
    if (phase !== 'recording') return;
    const off = onPoint((p) => setPoints((prev) => [...prev, p]));
    const tick = setInterval(() => setNow(Date.now()), 1000);
    const sub = AppState.addEventListener('change', async (s) => {
      if (s === 'active' && runId) {
        await syncNativeBuffer(runId);
        setPoints(getPoints(runId));
      }
    });
    return () => {
      off();
      clearInterval(tick);
      sub.remove();
    };
  }, [phase, runId]);

  const start = useCallback(async () => {
    setError(null);
    const perm = await ensurePermissions();
    if (!perm.ok) {
      setError('Location permission is needed to record a run.');
      setPhase('error');
      return;
    }
    const run = createRun(route?.slug ?? null);
    startedAt.current = run.started_at;
    setRunId(run.id);
    setPoints([]);
    await startEngine(run.id);
    setPhase('recording');
  }, [route?.slug]);

  const finish = useCallback(async () => {
    if (!runId) return;
    setPhase('saving');
    await stopEngine(runId);
    setStatus(runId, 'finished');
    setPoints(getPoints(runId));
    try {
      setActivityId(await uploadRun(runId));
      setPhase('saved');
    } catch (e) {
      // Saved on the phone; it uploads automatically when back online.
      setError(e instanceof Error ? e.message : 'Upload failed');
      setPhase('saved');
    }
  }, [runId]);

  const discard = useCallback(async () => {
    if (!runId) return;
    await stopEngine(runId);
    discardRun(runId);
    setRunId(null);
    setPoints([]);
    setPhase('idle');
  }, [runId]);

  const stats = useMemo(() => {
    const elapsed = startedAt.current && phase === 'recording' ? (now - startedAt.current) / 1000 : 0;
    const distance = liveDistance(points);
    const recent = points.filter((p) => p.t > now - 30_000);
    const recentDist = liveDistance(recent);
    const pace = distance > 50 ? elapsed / (distance / 1000) : null;
    const currentPace = recentDist > 20 && recent.length > 1 ? (recent[recent.length - 1].t - recent[0].t) / 1000 / (recentDist / 1000) : null;
    const lastAcc = points.length ? points[points.length - 1].acc : null;
    return { elapsed, distance, pace, currentPace, gps: lastAcc == null ? 'searching' : lastAcc <= 10 ? 'strong' : lastAcc <= 25 ? 'ok' : 'weak' };
  }, [points, now, phase]);

  const progress = useMemo(() => {
    if (!route) return null;
    const pt = (ll: [number, number]) => ({ lat: ll[0], lon: ll[1] });
    return checkpointProgress(points, pt(route.start), route.checkpoints.map(pt), pt(route.finish));
  }, [points, route]);

  return { phase, runId, points, stats, progress, error, activityId, start, finish, discard };
}
