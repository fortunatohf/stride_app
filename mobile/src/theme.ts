// Design tokens from the STRYDE mockups (docs). Dark, high contrast, volt for actions, gold for titles.
export const colors = {
  bg: '#0B0C0F',
  surface: '#15171C',
  surface2: '#1D2027',
  surface3: '#262A33',
  line: '#2B2F39',
  text: '#F3F4F6',
  muted: '#8C93A1',
  muted2: '#5E6573',
  volt: '#D7FF3A',
  gold: '#FFC83D',
  red: '#FF5A4E',
  cyan: '#56D2FF',
  violet: '#A78BFA',
} as const;

export const radius = { sm: 12, md: 16, lg: 20, pill: 999 } as const;
export const space = (n: number) => n * 4;

export const type = {
  h1: { fontSize: 30, fontWeight: '700' as const, letterSpacing: -0.6, color: colors.text },
  h2: { fontSize: 20, fontWeight: '600' as const, letterSpacing: -0.3, color: colors.text },
  h3: { fontSize: 15, fontWeight: '600' as const, color: colors.text },
  body: { fontSize: 15, color: colors.text },
  small: { fontSize: 13, color: colors.muted },
  kicker: { fontSize: 11.5, fontWeight: '700' as const, letterSpacing: 1.1, textTransform: 'uppercase' as const, color: colors.muted },
  bigNumber: { fontSize: 64, fontWeight: '800' as const, letterSpacing: -2, color: colors.text, fontVariant: ['tabular-nums' as const] },
};

export function formatDuration(seconds?: number | null): string {
  if (seconds == null) return '—';
  const s = Math.round(seconds);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  const mm = h ? String(m).padStart(2, '0') : String(m);
  return `${h ? `${h}:` : ''}${mm}:${String(sec).padStart(2, '0')}`;
}

export function formatPace(secondsPerKm?: number | null): string {
  if (!secondsPerKm || !isFinite(secondsPerKm)) return '—';
  return `${formatDuration(secondsPerKm)} /km`;
}

export function formatKm(meters?: number | null, digits = 2): string {
  if (meters == null) return '—';
  return (meters / 1000).toFixed(digits);
}
