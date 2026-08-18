import { useEffect, useRef } from 'react';
import { Animated, Easing, Pressable, StyleSheet, Text } from 'react-native';

import { colors, radius, spacing } from '../theme';

export type BannerTone = 'good' | 'bad';

export interface BannerMessage {
  /** Bump this to re-show the banner for a repeated message. */
  key: number;
  tone: BannerTone;
  text: string;
}

interface BannerProps {
  message: BannerMessage | null;
  onDismiss: () => void;
  /** Milliseconds before it hides itself. */
  duration?: number;
}

export function Banner({ message, onDismiss, duration = 3500 }: BannerProps) {
  const slide = useRef(new Animated.Value(0)).current;

  // Callers pass an inline arrow, so onDismiss is a new function on every
  // parent render. Depending on it directly would restart the hide timer each
  // time — and screens that re-render often (the thread on every message) would
  // keep a banner on screen forever.
  const dismissRef = useRef(onDismiss);
  dismissRef.current = onDismiss;

  useEffect(() => {
    if (!message) return;

    slide.setValue(0);

    Animated.timing(slide, {
      toValue: 1,
      duration: 180,
      easing: Easing.out(Easing.quad),
      useNativeDriver: true,
    }).start();

    const timeout = setTimeout(() => {
      Animated.timing(slide, {
        toValue: 0,
        duration: 180,
        easing: Easing.in(Easing.quad),
        useNativeDriver: true,
      }).start(({ finished }) => {
        if (finished) dismissRef.current();
      });
    }, duration);

    return () => clearTimeout(timeout);
    // Keyed on `key` alone: that is what makes a repeated identical message
    // re-animate, and nothing else here should restart the timer.
  }, [message?.key, duration, slide]);

  if (!message) return null;

  return (
    <Animated.View
      style={[
        styles.banner,
        message.tone === 'bad' ? styles.bad : styles.good,
        {
          opacity: slide,
          transform: [
            { translateY: slide.interpolate({ inputRange: [0, 1], outputRange: [-12, 0] }) },
          ],
        },
      ]}
    >
      <Pressable onPress={() => dismissRef.current()} accessibilityRole="button">
        <Text style={styles.text}>{message.text}</Text>
      </Pressable>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  banner: {
    marginHorizontal: spacing.lg,
    marginBottom: spacing.md,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
  },
  good: { backgroundColor: '#12281C', borderColor: colors.down },
  bad: { backgroundColor: '#2A1417', borderColor: colors.danger },
  text: { color: colors.text, fontSize: 14, lineHeight: 20, fontWeight: '600' },
});
