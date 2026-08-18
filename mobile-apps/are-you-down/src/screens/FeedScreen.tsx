import { useFocusEffect, useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useCallback, useRef, useState } from 'react';
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

import type { FeedRow } from '../api/drops';
import { isTerminalResponseError, respondToDrop } from '../api/responses';
import { Banner, type BannerMessage, type BannerTone } from '../components/Banner';
import { Button } from '../components/Button';
import { CategoryFilterBar } from '../components/CategoryFilterBar';
import { DropCard } from '../components/DropCard';
import { MyDropRow } from '../components/MyDropRow';
import { SafetyActions, type SafetyTarget } from '../components/SafetyActions';
import { Sheet } from '../components/Sheet';
import { useCurrentUser } from '../hooks/useAuth';
import { useCategories } from '../hooks/useCategories';
import { useFeed } from '../hooks/useFeed';
import type { AppStackParamList } from '../navigation/types';
import { colors, radius, spacing } from '../theme';
import type { ResponseType } from '../types/database';

type Navigation = NativeStackNavigationProp<AppStackParamList>;

export function FeedScreen() {
  const navigation = useNavigation<Navigation>();
  const { userId, profile } = useCurrentUser();
  const { menu } = useCategories();

  // Which category group the feed is narrowed to, or null for all of it. The
  // server does the narrowing; this is just the chip that's lit.
  const [group, setGroup] = useState<string | null>(null);
  const feed = useFeed(userId, group);

  const groupLabel = group ? (menu?.groupBySlug[group]?.label ?? null) : null;

  const [pending, setPending] = useState<Record<string, ResponseType>>({});
  const [banner, setBanner] = useState<BannerMessage | null>(null);
  const [safetyTarget, setSafetyTarget] = useState<SafetyTarget | null>(null);
  const bannerKey = useRef(0);

  const { refresh, removeDrop, removeDropsByAuthor } = feed;
  const isFirstFocus = useRef(true);

  // The initial load already happens in useFeed; only refetch when coming back
  // to the tab, e.g. after posting a drop.
  useFocusEffect(
    useCallback(() => {
      if (isFirstFocus.current) {
        isFirstFocus.current = false;
        return;
      }
      void refresh();
    }, [refresh]),
  );

  const showBanner = useCallback((tone: BannerTone, text: string) => {
    bannerKey.current += 1;
    setBanner({ key: bannerKey.current, tone, text });
  }, []);

  const clearPending = useCallback((dropId: string) => {
    setPending((current) => {
      const next = { ...current };
      delete next[dropId];
      return next;
    });
  }, []);

  const respond = useCallback(
    async (drop: FeedRow, type: ResponseType) => {
      // Marking it pending animates the card out straight away — the request
      // is still in flight at this point.
      setPending((current) =>
        current[drop.id] ? current : { ...current, [drop.id]: type },
      );

      try {
        await respondToDrop(drop.id, userId, type);
        removeDrop(drop.id);
        clearPending(drop.id);

        if (type === 'down') {
          showBanner('good', `You're in with ${drop.display_name}. Check Threads.`);
        }
      } catch (error) {
        const text = error instanceof Error ? error.message : String(error);

        if (isTerminalResponseError(error)) {
          // Closed, expired, full, or already answered — springing the card
          // back would only invite a second doomed tap.
          removeDrop(drop.id);
          clearPending(drop.id);
        } else {
          // Still answerable, so give it back.
          clearPending(drop.id);
        }

        showBanner('bad', text);
      }
    },
    [userId, removeDrop, clearPending, showBanner],
  );

  const handleDown = useCallback(
    (drop: FeedRow) => void respond(drop, 'down'),
    [respond],
  );

  const handlePass = useCallback(
    (drop: FeedRow) => void respond(drop, 'pass'),
    [respond],
  );

  const handleMore = useCallback(
    (drop: FeedRow) =>
      setSafetyTarget({
        type: 'drop',
        targetId: drop.id,
        subjectId: drop.author_id,
        subjectName: drop.display_name,
        preview: drop.body,
      }),
    [],
  );

  const openCreate = () => navigation.navigate('CreateDrop');

  const renderItem = useCallback(
    ({ item }: { item: FeedRow }) => (
      <DropCard
        drop={item}
        onDown={handleDown}
        onPass={handlePass}
        onMore={handleMore}
        leaving={pending[item.id] ?? null}
      />
    ),
    [handleDown, handlePass, handleMore, pending],
  );

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.header}>
        <View style={styles.headerText}>
          <Text style={styles.title}>Are you down?</Text>
          <Text style={styles.subtitle}>{profile.school.name}</Text>
        </View>

        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Post a drop"
          onPress={openCreate}
          style={({ pressed }) => [styles.fab, pressed ? styles.fabPressed : null]}
        >
          <Text style={styles.fabIcon}>+</Text>
        </Pressable>
      </View>

      <CategoryFilterBar value={group} onChange={setGroup} />

      <Banner message={banner} onDismiss={() => setBanner(null)} />

      <FlatList
        data={feed.drops}
        keyExtractor={(item) => item.id}
        renderItem={renderItem}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl
            refreshing={feed.refreshing}
            onRefresh={() => void feed.refresh()}
            tintColor={colors.textMuted}
          />
        }
        onEndReachedThreshold={0.4}
        onEndReached={() => void feed.loadMore()}
        ListHeaderComponent={
          feed.myDrops.length > 0 ? (
            <View style={styles.myDrops}>
              <Text style={styles.sectionLabel}>Your drops</Text>
              {feed.myDrops.map((drop) => (
                <MyDropRow key={drop.id} drop={drop} />
              ))}
            </View>
          ) : null
        }
        ListEmptyComponent={
          feed.status === 'loading' ? (
            <ActivityIndicator color={colors.accent} style={styles.spinner} />
          ) : feed.status === 'error' ? (
            <ErrorState message={feed.error} onRetry={() => void feed.refresh()} />
          ) : (
            <EmptyState
              groupLabel={groupLabel}
              onCreate={openCreate}
              onClearFilter={() => setGroup(null)}
            />
          )
        }
        ListFooterComponent={
          feed.loadingMore ? (
            <ActivityIndicator color={colors.textMuted} style={styles.spinner} />
          ) : null
        }
      />

      <Sheet
        visible={safetyTarget !== null}
        title={safetyTarget?.subjectName ?? ''}
        subtitle={safetyTarget?.preview}
        onClose={() => setSafetyTarget(null)}
      >
        {safetyTarget ? (
          <SafetyActions
            target={safetyTarget}
            currentUserId={userId}
            onClose={() => setSafetyTarget(null)}
            onBlocked={(authorId, name) => {
              removeDropsByAuthor(authorId);
              showBanner('good', `${name} is blocked. You won't see each other.`);
            }}
            onReported={() => showBanner('good', "Thanks — we'll take a look.")}
            onViewProfile={(id) => navigation.navigate('Person', { userId: id })}
            onError={(message) => showBanner('bad', message)}
          />
        ) : null}
      </Sheet>
    </SafeAreaView>
  );
}

function EmptyState({
  groupLabel,
  onCreate,
  onClearFilter,
}: {
  groupLabel: string | null;
  onCreate: () => void;
  onClearFilter: () => void;
}) {
  // An empty filtered feed is a different thing from an empty campus, and
  // saying "nobody has posted yet" while a filter is on would read as a bug.
  if (groupLabel) {
    return (
      <View style={styles.empty}>
        <Text style={styles.emptyEmoji}>🔍</Text>
        <Text style={styles.emptyTitle}>Nothing in {groupLabel} right now</Text>
        <Text style={styles.emptyBody}>
          Other groups might have something going on — or you could be the one
          who starts it.
        </Text>
        <Button
          label="Show everything"
          variant="secondary"
          onPress={onClearFilter}
          style={styles.emptyButton}
        />
        <Button label="Post something" onPress={onCreate} style={styles.emptyButton} />
      </View>
    );
  }

  return (
    <View style={styles.empty}>
      <Text style={styles.emptyEmoji}>🌵</Text>
      <Text style={styles.emptyTitle}>Nothing going on</Text>
      <Text style={styles.emptyBody}>
        Nobody has posted yet, which means whoever goes first decides what
        everyone's doing tonight. Might as well be you.
      </Text>
      <Button label="Post something" onPress={onCreate} style={styles.emptyButton} />
    </View>
  );
}

function ErrorState({
  message,
  onRetry,
}: {
  message: string | null;
  onRetry: () => void;
}) {
  return (
    <View style={styles.empty}>
      <Text style={styles.emptyTitle}>Couldn't load the feed</Text>
      <Text style={styles.emptyBody}>{message ?? 'Something went wrong.'}</Text>
      <Button
        label="Try again"
        variant="secondary"
        onPress={onRetry}
        style={styles.emptyButton}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.sm,
    paddingBottom: spacing.md,
    gap: spacing.md,
  },
  headerText: { gap: 2, flexShrink: 1 },
  title: { color: colors.text, fontSize: 26, fontWeight: '800', letterSpacing: -0.5 },
  subtitle: { color: colors.textMuted, fontSize: 13 },
  fab: {
    width: 44,
    height: 44,
    borderRadius: radius.pill,
    backgroundColor: colors.accent,
    alignItems: 'center',
    justifyContent: 'center',
  },
  fabPressed: { opacity: 0.75 },
  fabIcon: {
    color: colors.accentText,
    fontSize: 28,
    fontWeight: '600',
    lineHeight: 32,
    marginTop: -2,
  },
  // No `gap` here: each card owns its bottom margin so it can animate to zero
  // as the card collapses.
  list: { padding: spacing.lg, paddingTop: 0, flexGrow: 1 },
  myDrops: { gap: spacing.sm, marginBottom: spacing.lg },
  sectionLabel: {
    color: colors.textMuted,
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.6,
    textTransform: 'uppercase',
  },
  spinner: { marginVertical: spacing.xl },
  empty: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.xxl * 2,
    paddingHorizontal: spacing.lg,
    gap: spacing.md,
  },
  emptyEmoji: { fontSize: 40 },
  emptyTitle: { color: colors.text, fontSize: 20, fontWeight: '700' },
  emptyBody: {
    color: colors.textMuted,
    fontSize: 15,
    lineHeight: 22,
    textAlign: 'center',
  },
  emptyButton: { alignSelf: 'stretch', marginTop: spacing.sm },
});
