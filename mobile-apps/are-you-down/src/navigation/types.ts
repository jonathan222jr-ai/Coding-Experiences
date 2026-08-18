import type { NavigatorScreenParams } from '@react-navigation/native';

export type AppTabParamList = {
  Feed: undefined;
  Threads: undefined;
  Profile: undefined;
};

export type AppStackParamList = {
  Tabs: NavigatorScreenParams<AppTabParamList>;
  CreateDrop: undefined;
  Thread: { threadId: string };
  Person: { userId: string };
};

export type RootStackParamList = {
  Auth: undefined;
  App: NavigatorScreenParams<AppStackParamList>;
  ProfileError: undefined;
};
