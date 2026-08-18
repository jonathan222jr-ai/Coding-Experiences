import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { AuthProvider } from './src/hooks/useAuth';
import { CategoriesProvider } from './src/hooks/useCategories';
import { RootNavigator } from './src/navigation/RootNavigator';

export default function App() {
  return (
    <SafeAreaProvider>
      <StatusBar style="light" />
      <AuthProvider>
        <CategoriesProvider>
          <RootNavigator />
        </CategoriesProvider>
      </AuthProvider>
    </SafeAreaProvider>
  );
}
