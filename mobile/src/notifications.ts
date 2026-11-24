import Constants from 'expo-constants';
import * as Device from 'expo-device';
import * as Notifications from 'expo-notifications';
import { router } from 'expo-router';
import { Platform } from 'react-native';

import { api } from './api/client';

Notifications.setNotificationHandler({
  handleNotification: async () => ({ shouldShowBanner: true, shouldShowList: true, shouldPlaySound: true, shouldSetBadge: false }),
});

/** Ask permission and send the Expo push token to the backend (title-lost alerts). */
export async function registerForPush() {
  if (!Device.isDevice) return;
  const { status } = await Notifications.requestPermissionsAsync();
  if (status !== 'granted') return;
  const projectId = Constants.expoConfig?.extra?.eas?.projectId as string | undefined;
  if (!projectId) return; // run `eas init` to get a project id
  const token = await Notifications.getExpoPushTokenAsync({ projectId });
  await api('/api/me/push-tokens/', { body: { token: token.data, platform: Platform.OS } }).catch(() => undefined);
}

/** Tapping "Luis took Zilker Loop" opens that route. */
export function routeFromNotifications() {
  const sub = Notifications.addNotificationResponseReceivedListener((resp) => {
    const data = resp.notification.request.content.data as { route?: string };
    if (data?.route) router.push({ pathname: '/route/[slug]', params: { slug: data.route } });
  });
  return () => sub.remove();
}
