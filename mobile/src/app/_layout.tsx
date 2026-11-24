import '../recorder/engine'; // registers the background location task at startup

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Stack, router, useSegments } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useEffect, useState } from 'react';
import { AppState } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { getAccessToken, setAuthChangeHandler } from '../api/client';
import { registerForPush, routeFromNotifications } from '../notifications';
import { flushPendingUploads } from '../recorder/upload';
import { colors } from '../theme';

const queryClient = new QueryClient({ defaultOptions: { queries: { staleTime: 30_000, retry: 1 } } });

export default function RootLayout() {
  const [signedIn, setSignedIn] = useState<boolean | null>(null);
  const segments = useSegments();

  useEffect(() => {
    getAccessToken().then((t) => setSignedIn(!!t));
    setAuthChangeHandler((v) => {
      if (!v) queryClient.clear();
      setSignedIn(v);
    });
  }, []);

  useEffect(() => {
    if (signedIn === null) return;
    const inAuth = segments[0] === 'login';
    if (!signedIn && !inAuth) router.replace('/login');
    if (signedIn && inAuth) router.replace('/');
  }, [signedIn, segments]);

  useEffect(() => {
    if (!signedIn) return;
    flushPendingUploads();
    registerForPush();
    const offTap = routeFromNotifications();
    const sub = AppState.addEventListener('change', (s) => s === 'active' && flushPendingUploads());
    return () => {
      offTap();
      sub.remove();
    };
  }, [signedIn]);

  return (
    <SafeAreaProvider>
      <QueryClientProvider client={queryClient}>
        <StatusBar style="light" />
        <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: colors.bg } }}>
          <Stack.Screen name="(tabs)" />
          <Stack.Screen name="login" options={{ gestureEnabled: false }} />
          <Stack.Screen name="route/[slug]" />
          <Stack.Screen name="run/[activityId]" options={{ gestureEnabled: false }} />
          <Stack.Screen name="devices" options={{ presentation: 'modal' }} />
        </Stack>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}
