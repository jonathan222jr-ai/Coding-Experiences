import Constants from 'expo-constants';
import * as Device from 'expo-device';
import * as Notifications from 'expo-notifications';
import { useEffect } from 'react';
import { Platform } from 'react-native';

import { savePushToken } from '../api/push';
import { navigationRef } from '../navigation/navigationRef';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowBanner: true,
    shouldShowList: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

function projectId(): string | undefined {
  const eas = Constants.expoConfig?.extra?.eas as { projectId?: string } | undefined;
  return eas?.projectId;
}

/**
 * Register this device for the one notification the app sends, and route a tap
 * on it to the thread it is about.
 *
 * Everything here fails soft. Push is a nicety layered on top of a working app:
 * no EAS project, a declined permission, a simulator, or Expo Go on Android
 * (which has not supported remote push since SDK 53) should all mean "no
 * notifications", never "broken screen".
 */
export function usePushRegistration(userId: string | null): void {
  useEffect(() => {
    if (!userId) return;

    let active = true;

    void (async () => {
      try {
        // Simulators and emulators cannot be issued a push token.
        if (!Device.isDevice) return;

        // Android 13+ shows no permission prompt until a channel exists, and
        // the token request itself needs one.
        if (Platform.OS === 'android') {
          await Notifications.setNotificationChannelAsync('default', {
            name: 'Thread activity',
            importance: Notifications.AndroidImportance.DEFAULT,
          });
        }

        const existing = await Notifications.getPermissionsAsync();
        const status =
          existing.status === 'granted'
            ? existing.status
            : (await Notifications.requestPermissionsAsync()).status;

        if (status !== 'granted' || !active) return;

        const id = projectId();
        if (!id) {
          console.warn(
            'No EAS projectId in app.json (extra.eas.projectId) — skipping push registration. ' +
              'Run `eas init` to set one up.',
          );
          return;
        }

        const token = await Notifications.getExpoPushTokenAsync({ projectId: id });
        if (active) await savePushToken(userId, token.data);
      } catch (error) {
        console.warn('Push registration skipped:', error);
      }
    })();

    return () => {
      active = false;
    };
  }, [userId]);

  // Tapping the notification should land on the thread it announced.
  useEffect(() => {
    const subscription = Notifications.addNotificationResponseReceivedListener((response) => {
      const data = response.notification.request.content.data as { threadId?: string };

      if (data?.threadId && navigationRef.isReady()) {
        navigationRef.navigate('App', {
          screen: 'Thread',
          params: { threadId: data.threadId },
        });
      }
    });

    return () => subscription.remove();
  }, []);
}
