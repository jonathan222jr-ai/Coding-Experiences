import { useFocusEffect, useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { fetchThreads, type ThreadRow } from '../api/threads';
import { Button } from '../components/Button';
import { CategoryBadge } from '../components/CategoryChip';
import { useCategories } from '../hooks/useCategories';
import { useNow } from '../hooks/useNow';
import { formatAge } from '../lib/time';
import type { AppStackParamList } from '../navigation/types';
import { colors, radius, spacing } from '../theme';

type Navigation = NativeStackNavigationProp<AppStackParamList>;

export function ThreadsScreen() {
  const navigation = useNavigation<Navigation>();

  const [threads, setThreads] = useState<ThreadRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async ({ silent = false }: { silent?: boolean } = {}) => {
    if (!silent) setRefreshing(true);
    try {
      setThreads(await fetchThreads());
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      if (!silent) setRefreshing(false);
    }
  }, []);

  // Message previews go stale as soon as anyone types, so refetch whenever the
  // tab comes forward rather than only on mount. Silently, though — flashing
  // the pull-to-refresh spinner on every tab switch reads as a glitch.
  useFocusEffect(
    useCallback(() => {
      void load({ silent: true });
    }, [load]),
  );

  const renderItem = useCallback(
    ({ item }: { item: ThreadRow }) => (
      <ThreadRowItem
        thread={item}
        onPress={() => navigation.navigate('Thread', { threadId: item.thread_id })}
      />
    ),
    [navigation],
  );

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <Text style={styles.title}>Threads</Text>

      <FlatList
        data={threads ?? []}
        keyExtractor={(item) => item.thread_id}
        renderItem={renderItem}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => void load()}
            tintColor={colors.textMuted}
          />
        }
        ListEmptyComponent={
          threads === null && !error ? (
            <ActivityIndicator color={colors.accent} style={styles.spinner} />
          ) : error ? (
            <View style={styles.empty}>
              <Text style={styles.emptyTitle}>Couldn't load your threads</Text>
              <Text style={styles.emptyBody}>{error}</Text>
              <Button
                label="Try again"
                variant="secondary"
                onPress={() => void load()}
                style={styles.emptyButton}
              />
            </View>
          ) : (
            <View style={styles.empty}>
              <Text style={styles.emoji}>💬</Text>
              <Text style={styles.emptyTitle}>No threads yet</Text>
              <Text style={styles.emptyBody}>
                A thread opens the moment someone is down for your drop — or you
                are down for theirs.
              </Text>
            </View>
          )
        }
      />
    </SafeAreaView>
  );
}

function ThreadRowItem({
  thread,
  onPress,
}: {
  thread: ThreadRow;
  onPress: () => void;
}) {
  const now = useNow();
  const { describe } = useCategories();
  const category = describe(thread.drop_category);

  const preview = thread.last_message_body
    ? `${thread.last_message_author}: ${thread.last_message_body}`
    : 'No messages yet';

  const timestamp = thread.last_message_at ? formatAge(thread.last_message_at, now) : '';

  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      style={({ pressed }) => [styles.row, pressed ? styles.rowPressed : null]}
    >
      <CategoryBadge category={thread.drop_category} />

      <View style={styles.rowText}>
        <View style={styles.rowTop}>
          <Text style={styles.rowTitle} numberOfLines={1}>
            {thread.drop_body}
          </Text>
          {timestamp ? <Text style={styles.rowTime}>{timestamp}</Text> : null}
        </View>

        <Text style={styles.rowPreview} numberOfLines={1}>
          {preview}
        </Text>

        <Text style={[styles.rowMeta, { color: category.color }]}>
          {category.label}
          <Text style={styles.rowMetaRest}>
            {' · '}
            {thread.member_count} {thread.member_count === 1 ? 'person' : 'people'}
            {thread.drop_status !== 'open' ? ` · ${thread.drop_status}` : ''}
          </Text>
        </Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  title: {
    color: colors.text,
    fontSize: 26,
    fontWeight: '800',
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.sm,
    paddingBottom: spacing.md,
  },
  list: { paddingHorizontal: spacing.lg, gap: spacing.sm, flexGrow: 1 },
  row: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.md,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
  },
  rowPressed: { opacity: 0.75 },
  rowText: { flex: 1, gap: 3 },
  rowTop: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  rowTitle: { color: colors.text, fontSize: 15, fontWeight: '700', flex: 1 },
  rowTime: { color: colors.textMuted, fontSize: 12 },
  rowPreview: { color: colors.textMuted, fontSize: 14 },
  rowMeta: { fontSize: 12, fontWeight: '700' },
  rowMetaRest: { color: colors.textMuted, fontWeight: '400' },
  spinner: { marginVertical: spacing.xl },
  empty: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.md,
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.xxl * 2,
  },
  emoji: { fontSize: 40 },
  emptyTitle: { color: colors.text, fontSize: 20, fontWeight: '700' },
  emptyBody: {
    color: colors.textMuted,
    fontSize: 15,
    lineHeight: 22,
    textAlign: 'center',
  },
  emptyButton: { alignSelf: 'stretch', marginTop: spacing.sm },
});
