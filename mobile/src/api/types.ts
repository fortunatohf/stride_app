export type LatLon = [number, number];

export type Champion = { user_id: number; name: string; record_s: number; since: string | null } | null;

export type RouteSummary = {
  slug: string;
  name: string;
  city: string;
  distance_m: number;
  is_loop: boolean;
  status: string;
  start: LatLon;
  champion: Champion;
  title_changes: number;
};

export type RouteDetail = RouteSummary & {
  path: LatLon[];
  finish: LatLon;
  checkpoints: LatLon[];
  founder: string | null;
  history: { new_holder: string; previous_holder: string | null; previous_record_s: number | null; new_record_s: number; created_at: string }[];
};

export type LeaderboardRow = { rank: number; user_id: number; name: string; elapsed_s: number; me: boolean };

export type Attempt = {
  id: number;
  route: string;
  route_name: string;
  valid: boolean;
  eligible: boolean;
  elapsed_s: number | null;
  distance_m: number | null;
  reasons: string[];
  splits_s: number[];
  took_title: boolean;
  personal_best: boolean;
  start_time: string | null;
  created_at: string;
};

export type Activity = {
  id: number;
  source: string;
  device: string;
  started_at: string;
  duration_s: number;
  distance_m: number;
  state: 'received' | 'processed' | 'failed';
  path: LatLon[];
  attempts: Attempt[];
};

export type League = {
  season: { city: string; number: number; starts_on: string; ends_on: string } | null;
  tier?: string;
  weekly_cap?: number;
  points_table?: Record<string, number>;
  standings?: { rank: number; user_id: number; name: string; points: number; me: boolean }[];
};

export type TrainingSession = {
  id: number;
  date: string;
  kind: 'rest' | 'easy' | 'tempo' | 'intervals' | 'shakeout' | 'attempt';
  title: string;
  detail: string;
  minutes: number | null;
  completed_at: string | null;
};

export type TrainingPlan = {
  id: number;
  kind: string;
  title: string;
  route: string | null;
  goal_time_s: number | null;
  starts_on: string;
  attempt_on: string | null;
  sessions: TrainingSession[];
};

export type Integrations = {
  on_device: { key: string; name: string; covers: string; status: string; platform: string }[];
  cloud: { key: string; name: string; status: string; available: boolean; connected: boolean }[];
  post_watch_runs: boolean;
};

export type Me = {
  id: number;
  username: string;
  display_name: string;
  city: string;
  language: string;
  post_watch_runs: boolean;
  is_premium: boolean;
  xp: number;
};

export type Paged<T> = { count: number; results: T[] };

export type Alert = {
  type: 'title_lost';
  route: string;
  route_name: string;
  distance_m: number;
  by: string;
  their_time_s: number;
  your_time_s: number | null;
  at: string;
};
