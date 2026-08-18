import { createNavigationContainerRef } from '@react-navigation/native';

import type { RootStackParamList } from './types';

/**
 * Lets code outside the React tree — the push notification response handler —
 * navigate. Always guard with `navigationRef.isReady()`: a notification can be
 * tapped before the container has mounted.
 */
export const navigationRef = createNavigationContainerRef<RootStackParamList>();
