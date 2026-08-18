import { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button } from '../components/Button';
import { useAuth } from '../hooks/useAuth';
import { colors, spacing } from '../theme';

/**
 * Shown when we hold a session but the profile behind it won't load — almost
 * always a dead network on a cold start. Retrying is usually enough; signing
 * out is the escape hatch if it isn't.
 */
export function ProfileErrorScreen() {
  const { profileError, refreshProfile, signOut } = useAuth();
  const [busy, setBusy] = useState(false);

  const run = async (action: () => Promise<void>) => {
    setBusy(true);
    try {
      await action();
    } catch {
      // The error is already reflected in context.
    } finally {
      setBusy(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.content}>
        <Text style={styles.title}>Can't load your profile</Text>
        <Text style={styles.body}>
          {profileError ?? 'Check your connection and try again.'}
        </Text>

        <Button label="Try again" onPress={() => void run(refreshProfile)} loading={busy} />
        <Button
          label="Sign out"
          variant="ghost"
          onPress={() => void run(signOut)}
          disabled={busy}
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  content: {
    flex: 1,
    padding: spacing.xl,
    justifyContent: 'center',
    gap: spacing.lg,
  },
  title: { color: colors.text, fontSize: 26, fontWeight: '800' },
  body: { color: colors.textMuted, fontSize: 15, lineHeight: 22 },
});
