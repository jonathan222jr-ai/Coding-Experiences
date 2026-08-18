import { memo, useEffect, useRef, useState } from 'react';
import {
  Animated,
  Easing,
  Pressable,
  StyleSheet,
  Text,
  useWindowDimensions,
  View,
  type LayoutChangeEvent,
} from 'react-native';

import { useNow } from '../hooks/useNow';
import { formatRemaining, isUrgent } from '../lib/time';
import { colors, radius, spacing } from '../theme';
import type { FeedRow, ResponseType } from '../types/database';
import { Button } from './Button';
import { CategoryChip } from './CategoryChip';
import { GifImage } from './GifImage';

/** The feed's own padding, plus the card's, on both sides. */
const CARD_INSET = spacing.lg * 4;

interface DropCardProps {
  drop: FeedRow;
  onDown: (drop: FeedRow) => void;
  onPass: (drop: FeedRow) => void;
  onMore: (drop: FeedRow) => void;
  /**
   * Non-null while a response is in flight. The card animates out immediately
   * and stays collapsed; if the request fails this goes back to null and the
   * card springs back in.
   */
  leaving?: ResponseType | null;
}

const EXIT_MS = 240;

function DropCardComponent({ drop, onDown, onPass, onMore, leaving = null }: DropCardProps) {
  const now = useNow();
  const { width } = useWindowDimensions();
  const remaining = formatRemaining(drop.expires_at, now);
  const urgent = isUrgent(drop.expires_at, now);

  // 0 = fully present, 1 = fully gone.
  const exit = useRef(new Animated.Value(0)).current;
  const [height, setHeight] = useState<number | null>(null);

  // Remember which way to fly out, so the return trip doesn't snap direction
  // the instant `leaving` clears.
  const direction = useRef<ResponseType>('pass');
  if (leaving) direction.current = leaving;

  useEffect(() => {
    Animated.timing(exit, {
      toValue: leaving ? 1 : 0,
      duration: EXIT_MS,
      easing: leaving ? Easing.in(Easing.cubic) : Easing.out(Easing.cubic),
      // Collapsing the height rules out the native driver, and mixing drivers
      // on one node throws. Only one card animates at a time, so this is fine.
      useNativeDriver: false,
    }).start();
  }, [leaving, exit]);

  const onLayout = (event: LayoutChangeEvent) => {
    const measured = event.nativeEvent.layout.height;
    // Measure once, while the card is at rest — re-measuring mid-collapse
    // would feed the animation its own output.
    if (height === null && measured > 0) {
      setHeight(measured);
    }
  };

  const collapse = {
    opacity: exit.interpolate({ inputRange: [0, 1], outputRange: [1, 0] }),
    transform: [
      {
        translateX: exit.interpolate({
          inputRange: [0, 1],
          outputRange: [0, direction.current === 'down' ? 420 : -420],
        }),
      },
    ],
    ...(height !== null
      ? {
          height: exit.interpolate({ inputRange: [0, 1], outputRange: [height, 0] }),
          marginBottom: exit.interpolate({
            inputRange: [0, 1],
            outputRange: [spacing.md, 0],
          }),
        }
      : { marginBottom: spacing.md }),
  };

  return (
    <Animated.View style={[styles.wrapper, collapse]}>
      <View style={styles.card} onLayout={onLayout}>
        <View style={styles.topRow}>
          <CategoryChip category={drop.category} />

          <View style={styles.topRight}>
            <Text style={[styles.timer, urgent ? styles.timerUrgent : null]}>{remaining}</Text>

            <Pressable
              accessibilityRole="button"
              accessibilityLabel={`Report or block ${drop.display_name}`}
              hitSlop={10}
              onPress={() => onMore(drop)}
              style={({ pressed }) => [styles.more, pressed ? styles.morePressed : null]}
            >
              <Text style={styles.moreIcon}>⋯</Text>
            </Pressable>
          </View>
        </View>

        <Text style={styles.body}>{drop.body}</Text>

        {/* The GIF is an addition to the sentence, never a replacement — a
            drop's body is NOT NULL, so this is always below real text. */}
        {drop.gif_url ? (
          <GifImage
            url={drop.gif_url}
            width={drop.gif_width}
            height={drop.gif_height}
            alt={drop.gif_alt}
            maxWidth={width - CARD_INSET}
          />
        ) : null}

        <Text style={styles.author}>{drop.display_name}</Text>

        <View style={styles.actions}>
          <Button
            label="Pass"
            variant="secondary"
            onPress={() => onPass(drop)}
            disabled={leaving !== null}
            style={styles.action}
          />
          <Button
            label="I'm down"
            onPress={() => onDown(drop)}
            disabled={leaving !== null}
            style={styles.action}
          />
        </View>
      </View>
    </Animated.View>
  );
}

/**
 * The feed re-renders every second from the shared clock, so skip cards whose
 * data hasn't actually changed — the countdown reads the clock itself.
 */
export const DropCard = memo(DropCardComponent);

const styles = StyleSheet.create({
  wrapper: { overflow: 'hidden' },
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
    gap: spacing.md,
  },
  topRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  topRight: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  timer: { color: colors.textMuted, fontSize: 13, fontWeight: '600' },
  more: { paddingHorizontal: spacing.xs },
  morePressed: { opacity: 0.6 },
  moreIcon: { color: colors.textMuted, fontSize: 20, fontWeight: '800', lineHeight: 22 },
  timerUrgent: { color: colors.accent },
  body: { color: colors.text, fontSize: 19, lineHeight: 26, fontWeight: '600' },
  author: { color: colors.textMuted, fontSize: 14 },
  actions: { flexDirection: 'row', gap: spacing.md, marginTop: spacing.xs },
  action: { flex: 1 },
});
