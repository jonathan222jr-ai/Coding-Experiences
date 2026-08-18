import { Image } from 'expo-image';
import { StyleSheet, View, type StyleProp, type ViewStyle } from 'react-native';

import { colors, radius } from '../theme';

interface GifImageProps {
  url: string;
  /** Tenor's dimensions. Either may be null; see the ratio note below. */
  width: number | null;
  height: number | null;
  alt: string | null;
  /** The box to fit into. Height follows from the GIF's aspect ratio. */
  maxWidth: number;
  style?: StyleProp<ViewStyle>;
}

/**
 * A Tenor GIF at a known width.
 *
 * Shared by message bubbles and drop cards so both reserve the right box
 * *before* the image loads — without that the list jumps as GIFs arrive, which
 * is at its worst in the inverted chat list.
 */
export function GifImage({ url, width, height, alt, maxWidth, style }: GifImageProps) {
  // Tenor sometimes omits dims. 1:1 is a less disruptive guess than 0, which
  // would collapse the box and then shove the list when the image lands.
  const ratio = width && height ? width / height : 1;

  return (
    <View style={[styles.frame, style]}>
      <Image
        source={{ uri: url }}
        style={{ width: maxWidth, height: Math.round(maxWidth / ratio) }}
        contentFit="cover"
        transition={120}
        accessibilityLabel={alt ?? 'GIF'}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  frame: {
    borderRadius: radius.lg,
    overflow: 'hidden',
    backgroundColor: colors.surfaceRaised,
  },
});
