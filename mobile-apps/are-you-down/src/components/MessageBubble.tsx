import { memo } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { useNow } from '../hooks/useNow';
import { formatAge } from '../lib/time';
import { colors, radius, spacing } from '../theme';
import { GifImage } from './GifImage';

const GIF_MAX_WIDTH = 220;

interface MessageBubbleProps {
  body: string | null;
  gifUrl: string | null;
  gifWidth: number | null;
  gifHeight: number | null;
  gifAlt: string | null;
  createdAt: string;
  authorName: string;
  mine: boolean;
  /** False when the previous bubble is from the same person, to group runs. */
  showAuthor: boolean;
  /** Long-press opens report/block for this message. */
  onLongPress: () => void;
}

function MessageBubbleComponent({
  body,
  gifUrl,
  gifWidth,
  gifHeight,
  gifAlt,
  createdAt,
  authorName,
  mine,
  showAuthor,
  onLongPress,
}: MessageBubbleProps) {
  const now = useNow();

  return (
    <View style={[styles.row, mine ? styles.rowMine : styles.rowTheirs]}>
      {showAuthor && !mine ? <Text style={styles.author}>{authorName}</Text> : null}

      {gifUrl ? (
        <Pressable
          onLongPress={onLongPress}
          delayLongPress={350}
          accessibilityRole="image"
          accessibilityLabel={gifAlt ?? 'GIF'}
          accessibilityHint="Long press to report this message"
          style={({ pressed }) => (pressed ? styles.pressed : null)}
        >
          <GifImage
            url={gifUrl}
            width={gifWidth}
            height={gifHeight}
            alt={gifAlt}
            maxWidth={GIF_MAX_WIDTH}
          />
        </Pressable>
      ) : null}

      {body ? (
        <Pressable
          onLongPress={onLongPress}
          delayLongPress={350}
          accessibilityRole="button"
          accessibilityHint="Long press to report this message"
          style={({ pressed }) => [
            styles.bubble,
            mine ? styles.bubbleMine : styles.bubbleTheirs,
            gifUrl ? styles.bubbleUnderGif : null,
            pressed ? styles.pressed : null,
          ]}
        >
          <Text style={[styles.body, mine ? styles.bodyMine : null]}>{body}</Text>
        </Pressable>
      ) : null}

      <Text style={styles.time}>{formatAge(createdAt, now)}</Text>
    </View>
  );
}

export const MessageBubble = memo(MessageBubbleComponent);

const styles = StyleSheet.create({
  row: { marginBottom: spacing.md, maxWidth: '82%', gap: 3 },
  rowMine: { alignSelf: 'flex-end', alignItems: 'flex-end' },
  rowTheirs: { alignSelf: 'flex-start', alignItems: 'flex-start' },
  author: { color: colors.textMuted, fontSize: 12, fontWeight: '600', marginLeft: spacing.sm },
  bubble: {
    paddingHorizontal: spacing.lg - 2,
    paddingVertical: spacing.md - 2,
    borderRadius: radius.lg,
  },
  bubbleUnderGif: { marginTop: 2 },
  pressed: { opacity: 0.75 },
  bubbleMine: { backgroundColor: colors.accent, borderBottomRightRadius: radius.sm },
  bubbleTheirs: { backgroundColor: colors.surfaceRaised, borderBottomLeftRadius: radius.sm },
  body: { color: colors.text, fontSize: 16, lineHeight: 22 },
  bodyMine: { color: colors.accentText },
  time: { color: colors.textMuted, fontSize: 11, marginHorizontal: spacing.sm },
});
