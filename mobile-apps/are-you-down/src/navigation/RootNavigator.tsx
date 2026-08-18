import { DarkTheme, NavigationContainer, type Theme } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

import { LoadingScreen } from '../components/LoadingScreen';
import { useAuth } from '../hooks/useAuth';
import { AuthScreen } from '../screens/AuthScreen';
import { ProfileErrorScreen } from '../screens/ProfileErrorScreen';
import { colors } from '../theme';
import { AppNavigator } from './AppNavigator';
import { navigationRef } from './navigationRef';
import type { RootStackParamList } from './types';

const Stack = createNativeStackNavigator<RootStackParamList>();

const navigationTheme: Theme = {
  ...DarkTheme,
  colors: {
    ...DarkTheme.colors,
    background: colors.bg,
    card: colors.surface,
    text: colors.text,
    border: colors.border,
    primary: colors.accent,
  },
};

export function RootNavigator() {
  const { status, profile, profileError } = useAuth();

  if (status === 'loading') {
    return <LoadingScreen />;
  }

  // A session with no profile yet: either still in flight, or it failed and we
  // owe the user a retry. Screens behind this point can assume both exist.
  const awaitingProfile = status === 'signedIn' && !profile;

  if (awaitingProfile && !profileError) {
    return <LoadingScreen />;
  }

  return (
    <NavigationContainer ref={navigationRef} theme={navigationTheme}>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {status !== 'signedIn' ? (
          <Stack.Screen name="Auth" component={AuthScreen} />
        ) : awaitingProfile ? (
          <Stack.Screen name="ProfileError" component={ProfileErrorScreen} />
        ) : (
          <Stack.Screen name="App" component={AppNavigator} />
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
