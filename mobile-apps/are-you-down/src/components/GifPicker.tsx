import { Image } from 'expo-image';
import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { GifSearchError, searchGifs, type Gif } from '../api/gifs';
import { colors, radius, spacing } from '../theme';
import { Button } from './Button';

const COLUMN_WIDTH = 150;

interface GifPickerProps {
  onPick: (gif: Gif) => void;
}

export function GifPicker({ onPick }: GifPickerProps) {
  const [query, setQuery] = useState('');
  const [gifs, setGifs] = useState<Gif[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<GifSearchError | null>(null);
  // Bumped by the retry button to re-run the effect with the same query.
  const [attempt, setAttempt] = useState(0);

  const load = useCallback(async (term: string, signal: { cancelled: boolean }) => {
    setLoading(true);
    try {
      const results = await searchGifs(term);
      if (signal.cancelled) return;
      setGifs(results);
      setError(null);
    } catch (e) {
      if (signal.cancelled) return;
      setGifs([]);
      setError(
        e instanceof GifSearchError
          ? e
          : new GifSearchError(e instanceof Error ? e.message : String(e)),
      );
    } finally {
      if (!signal.cancelled) setLoading(false);
    }
  }, []);

  // Debounced: typing "excited" would otherwise fire seven searches, and every
  // one of them costs a request against the Tenor key.
  useEffect(() => {
    const signal = { cancelled: false };
    const timer = setTimeout(() => void load(query, signal), 300);

    return () => {
      signal.cancelled = true;
      clearTimeout(timer);
    };
  }, [query, attempt, load]);

  const renderItem = useCallback(
    ({ item }: { item: Gif }) => {
      const ratio = item.width && item.height ? item.width / item.height : 1;

      return (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={item.alt}
          onPress={() => onPick(item)}
          style={({ pressed }) => [styles.cell, pressed ? styles.cellPressed : null]}
        >
          <Image
            source={{ uri: item.previewUrl }}
            style={{ width: '100%', height: Math.round(COLUMN_WIDTH / ratio) }}
            contentFit="cover"
            transition={100}
          />
        </Pressable>
      );
    },
    [onPick],
  );

  const trimmed = query.trim();

  return (
    <View style={styles.container}>
      <TextInput
        value={query}
        onChangeText={setQuery}
        placeholder="Search GIFs"
        placeholderTextColor={colors.textMuted}
        style={styles.search}
        autoCapitalize="none"
        autoCorrect={false}
        returnKeyType="search"
      />

      {error ? (
        <View style={styles.state}>
          <Text style={styles.stateTitle}>{error.message}</Text>

          {/* A missing key is a deploy, not a network blip. Saying "try again"
              to someone who can only wait is worse than saying nothing. */}
          <Text style={styles.stateBody}>
            {error.unconfigured
              ? 'The GIF proxy has no Tenor key yet, so search is off. Messages still send.'
              : 'Tenor might be having a moment.'}
          </Text>

          {error.unconfigured ? null : (
            <Button
              label="Try again"
              variant="secondary"
              onPress={() => setAttempt((n) => n + 1)}
              style={styles.stateButton}
            />
          )}
        </View>
      ) : loading && gifs.length === 0 ? (
        <ActivityIndicator color={colors.accent} style={styles.spinner} />
      ) : gifs.length === 0 ? (
        <View style={styles.state}>
          <Text style={styles.stateTitle}>Nothing for “{trimmed}”.</Text>
          <Text style={styles.stateBody}>Try a shorter word.</Text>
        </View>
      ) : (
        <>
          {/* Says what the grid is. Without it, the featured set on open looks
              like the results of a search nobody typed. */}
          <Text style={styles.heading}>
            {trimmed.length > 0 ? `Results for “${trimmed}”` : 'Trending'}
          </Text>

          <FlatList
            data={gifs}
            keyExtractor={(item) => item.id}
            renderItem={renderItem}
            numColumns={2}
            columnWrapperStyle={styles.column}
            contentContainerStyle={styles.grid}
            keyboardShouldPersistTaps="handled"
          />
        </>
      )}

      <Text style={styles.credit}>GIFs via Tenor</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { height: 420, gap: spacing.md },
  search: {
    backgroundColor: colors.surfaceRaised,
    borderRadius: radius.md,
    color: colors.text,
    fontSize: 16,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
  },
  heading: {
    color: colors.textMuted,
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 0.6,
    textTransform: 'uppercase',
    marginBottom: -spacing.xs,
  },
  grid: { gap: spacing.sm, paddingBottom: spacing.md },
  column: { gap: spacing.sm },
  cell: {
    flex: 1,
    borderRadius: radius.md,
    overflow: 'hidden',
    backgroundColor: colors.surfaceRaised,
  },
  cellPressed: { opacity: 0.7 },
  spinner: { marginVertical: spacing.xxl },
  state: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    paddingHorizontal: spacing.lg,
  },
  stateTitle: { color: colors.text, fontSize: 16, fontWeight: '700', textAlign: 'center' },
  stateBody: {
    color: colors.textMuted,
    fontSize: 14,
    lineHeight: 20,
    textAlign: 'center',
  },
  stateButton: { alignSelf: 'stretch', marginTop: spacing.sm },
  credit: { color: colors.textMuted, fontSize: 11, textAlign: 'center' },
});
