import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StyleSheet, Text } from 'react-native';

import { useCurrentUser } from '../hooks/useAuth';
import { usePushRegistration } from '../hooks/usePushRegistration';
import { CreateDropScreen } from '../screens/CreateDropScreen';
import { FeedScreen } from '../screens/FeedScreen';
import { PersonScreen } from '../screens/PersonScreen';
import { ProfileScreen } from '../screens/ProfileScreen';
import { ThreadScreen } from '../screens/ThreadScreen';
import { ThreadsScreen } from '../screens/ThreadsScreen';
import { colors } from '../theme';
import type { AppStackParamList, AppTabParamList } from './types';

const Tab = createBottomTabNavigator<AppTabParamList>();
const Stack = createNativeStackNavigator<AppStackParamList>();

function tabIcon(glyph: string) {
  return function TabIcon({ focused }: { focused: boolean }) {
    return <Text style={[styles.icon, focused ? styles.iconOn : null]}>{glyph}</Text>;
  };
}

function Tabs() {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarStyle: styles.tabBar,
        tabBarActiveTintColor: colors.text,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarLabelStyle: styles.tabLabel,
      }}
    >
      <Tab.Screen
        name="Feed"
        component={FeedScreen}
        options={{ tabBarIcon: tabIcon('👀') }}
      />
      <Tab.Screen
        name="Threads"
        component={ThreadsScreen}
        options={{ tabBarIcon: tabIcon('💬') }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{ tabBarIcon: tabIcon('🙂') }}
      />
    </Tab.Navigator>
  );
}

export function AppNavigator() {
  const { userId } = useCurrentUser();

  // Only ever runs behind a session, which is exactly when a push token is
  // worth storing.
  usePushRegistration(userId);

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="Tabs" component={Tabs} />
      <Stack.Screen name="Thread" component={ThreadScreen} />
      <Stack.Screen name="Person" component={PersonScreen} />
      <Stack.Screen
        name="CreateDrop"
        component={CreateDropScreen}
        options={{ presentation: 'modal' }}
      />
    </Stack.Navigator>
  );
}

const styles = StyleSheet.create({
  tabBar: {
    backgroundColor: colors.surface,
    borderTopColor: colors.border,
  },
  tabLabel: { fontSize: 11, fontWeight: '600' },
  icon: { fontSize: 18, opacity: 0.5 },
  iconOn: { opacity: 1 },
});
