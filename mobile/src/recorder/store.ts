import * as Crypto from 'expo-crypto';
import * as SQLite from 'expo-sqlite';

/** Every GPS point is written here first, so a crash, a dead battery or no signal never loses a run. */
export type StoredPoint = { t: number; lat: number; lon: number; alt: number | null; acc: number | null; speed: number | null };
export type RunRow = {
  id: string;
  started_at: number;
  status: 'recording' | 'finished' | 'uploaded';
  route_slug: string | null;
  activity_id: number | null;
};

let db: SQLite.SQLiteDatabase | null = null;

export function getDb(): SQLite.SQLiteDatabase {
  if (db) return db;
  db = SQLite.openDatabaseSync('stryde.db');
  db.execSync(`
    PRAGMA journal_mode = WAL;
    CREATE TABLE IF NOT EXISTS runs (
      id TEXT PRIMARY KEY NOT NULL,
      started_at INTEGER NOT NULL,
      status TEXT NOT NULL,
      route_slug TEXT,
      activity_id INTEGER,
      native_index INTEGER NOT NULL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS points (
      run_id TEXT NOT NULL,
      t REAL NOT NULL,
      lat REAL NOT NULL,
      lon REAL NOT NULL,
      alt REAL,
      acc REAL,
      speed REAL,
      PRIMARY KEY (run_id, t)
    );
  `);
  return db;
}

export function createRun(routeSlug: string | null): RunRow {
  const run: RunRow = { id: Crypto.randomUUID(), started_at: Date.now(), status: 'recording', route_slug: routeSlug, activity_id: null };
  getDb().runSync('INSERT INTO runs (id, started_at, status, route_slug) VALUES (?, ?, ?, ?)', [
    run.id,
    run.started_at,
    run.status,
    routeSlug,
  ]);
  return run;
}

export function activeRun(): RunRow | null {
  return getDb().getFirstSync<RunRow>("SELECT * FROM runs WHERE status = 'recording' ORDER BY started_at DESC LIMIT 1");
}

export function addPoints(runId: string, pts: StoredPoint[]) {
  const d = getDb();
  d.withTransactionSync(() => {
    for (const p of pts) {
      d.runSync('INSERT OR IGNORE INTO points (run_id, t, lat, lon, alt, acc, speed) VALUES (?, ?, ?, ?, ?, ?, ?)', [
        runId,
        p.t,
        p.lat,
        p.lon,
        p.alt,
        p.acc,
        p.speed,
      ]);
    }
  });
}

export function getPoints(runId: string): StoredPoint[] {
  return getDb().getAllSync<StoredPoint>('SELECT t, lat, lon, alt, acc, speed FROM points WHERE run_id = ? ORDER BY t', [runId]);
}

export function setStatus(runId: string, status: RunRow['status'], activityId?: number) {
  getDb().runSync('UPDATE runs SET status = ?, activity_id = COALESCE(?, activity_id) WHERE id = ?', [status, activityId ?? null, runId]);
}

export function getNativeIndex(runId: string): number {
  return getDb().getFirstSync<{ native_index: number }>('SELECT native_index FROM runs WHERE id = ?', [runId])?.native_index ?? 0;
}

export function setNativeIndex(runId: string, index: number) {
  getDb().runSync('UPDATE runs SET native_index = ? WHERE id = ?', [index, runId]);
}

export function pendingUploads(): RunRow[] {
  return getDb().getAllSync<RunRow>("SELECT * FROM runs WHERE status = 'finished' ORDER BY started_at");
}

export function discardRun(runId: string) {
  const d = getDb();
  d.runSync('DELETE FROM points WHERE run_id = ?', [runId]);
  d.runSync('DELETE FROM runs WHERE id = ?', [runId]);
}
