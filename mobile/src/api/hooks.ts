import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { api } from './client';
import type {
  Activity,
  Alert,
  Attempt,
  Integrations,
  League,
  LeaderboardRow,
  Me,
  Paged,
  RouteDetail,
  RouteSummary,
  TrainingPlan,
} from './types';

export const useAlerts = () => useQuery({ queryKey: ['alerts'], queryFn: () => api<Alert[]>('/api/me/alerts/') });

export const useMe = () => useQuery({ queryKey: ['me'], queryFn: () => api<Me>('/api/me/') });

export const useNearbyRoutes = (center?: { lat: number; lon: number }, radiusKm = 15) =>
  useQuery({
    queryKey: ['routes', center?.lat.toFixed(2), center?.lon.toFixed(2), radiusKm],
    queryFn: () =>
      api<Paged<RouteSummary>>(
        center ? `/api/routes/?lat=${center.lat}&lon=${center.lon}&radius_km=${radiusKm}&limit=100` : '/api/routes/?limit=100',
      ).then((p) => p.results),
  });

export const useRoute = (slug: string) =>
  useQuery({ queryKey: ['route', slug], queryFn: () => api<RouteDetail>(`/api/routes/${slug}/`), enabled: !!slug });

export const useLeaderboard = (slug: string) =>
  useQuery({
    queryKey: ['leaderboard', slug],
    queryFn: () => api<{ rows: LeaderboardRow[]; record_s: number | null }>(`/api/routes/${slug}/leaderboard/`),
    enabled: !!slug,
  });

export const useActivities = () =>
  useQuery({ queryKey: ['activities'], queryFn: () => api<Paged<Activity>>('/api/activities/').then((p) => p.results) });

export const useActivity = (id?: number) =>
  useQuery({
    queryKey: ['activity', id],
    queryFn: () => api<Activity>(`/api/activities/${id}/`),
    enabled: !!id,
    // Poll while the server validates the run against nearby routes.
    refetchInterval: (q) => (q.state.data?.state === 'received' ? 1500 : false),
  });

export const useMyAttempts = () =>
  useQuery({ queryKey: ['attempts'], queryFn: () => api<Paged<Attempt>>('/api/attempts/').then((p) => p.results) });

export const useLeague = () => useQuery({ queryKey: ['league'], queryFn: () => api<League>('/api/leagues/current/') });

export const usePlan = () => useQuery({ queryKey: ['plan'], queryFn: () => api<TrainingPlan | null>('/api/training/current/') });

export const useIntegrations = () => useQuery({ queryKey: ['integrations'], queryFn: () => api<Integrations>('/api/integrations/') });

export function useCreateComeback() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (route: string) => api<TrainingPlan>('/api/training/comeback/', { body: { route } }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['plan'] }),
  });
}

export function useCompleteSession() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api(`/api/training/sessions/${id}/complete/`, { method: 'POST' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['plan'] }),
  });
}

export function usePublishRoute() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (args: { activity_id: number; name: string }) => api<RouteDetail>('/api/routes/', { body: args }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['routes'] }),
  });
}

export function useUpdateMe() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (patch: Partial<Me>) => api<Me>('/api/me/', { method: 'PATCH', body: patch }),
    onSuccess: (me) => qc.setQueryData(['me'], me),
  });
}
