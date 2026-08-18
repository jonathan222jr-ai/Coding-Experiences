import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { blockUser, reportContent } from '../api/safety';
import { colors, radius, spacing } from '../theme';
import type { ReportTarget } from '../types/database';
import { Button } from './Button';

export interface SafetyTarget {
  type: ReportTarget;
  /** id of the drop, message, or user being reported. */
  targetId: string;
  /** The person who would be blocked — the content's author. */
  subjectId: string;
  subjectName: string;
  /** Short excerpt shown so it's obvious what's being acted on. */
  preview?: string;
}

const REPORT_REASONS = [
  'Spam or a scam',
  'Harassment or bullying',
  'Sexual or explicit content',
  'Threat or safety concern',
  'Something else',
] as const;

interface SafetyActionsProps {
  target: SafetyTarget;
  currentUserId: string;
  onBlocked: (userId: string, name: string) => void;
  onReported: () => void;
  onError: (message: string) => void;
  onClose: () => void;
  /** Omitted on the person screen itself, where there is nowhere further to go. */
  onViewProfile?: (userId: string) => void;
}

type Step = 'menu' | 'report' | 'confirmBlock';

export function SafetyActions({
  target,
  currentUserId,
  onBlocked,
  onReported,
  onError,
  onClose,
  onViewProfile,
}: SafetyActionsProps) {
  const [step, setStep] = useState<Step>('menu');
  const [busy, setBusy] = useState(false);

  const noun =
    target.type === 'drop' ? 'drop' : target.type === 'message' ? 'message' : 'person';

  const submitReport = async (reason: string) => {
    setBusy(true);
    try {
      await reportContent(currentUserId, target.type, target.targetId, reason);
      onReported();
      onClose();
    } catch (error) {
      onError(error instanceof Error ? error.message : String(error));
      setBusy(false);
    }
  };

  const submitBlock = async () => {
    setBusy(true);
    try {
      await blockUser(currentUserId, target.subjectId);
      onBlocked(target.subjectId, target.subjectName);
      onClose();
    } catch (error) {
      onError(error instanceof Error ? error.message : String(error));
      setBusy(false);
    }
  };

  if (step === 'report') {
    return (
      <View style={styles.group}>
        <Text style={styles.prompt}>What's wrong with this {noun}?</Text>

        {REPORT_REASONS.map((reason) => (
          <Pressable
            key={reason}
            accessibilityRole="button"
            disabled={busy}
            onPress={() => void submitReport(reason)}
            style={({ pressed }) => [styles.option, pressed ? styles.optionPressed : null]}
          >
            <Text style={styles.optionText}>{reason}</Text>
          </Pressable>
        ))}

        <Button label="Back" variant="ghost" onPress={() => setStep('menu')} disabled={busy} />
      </View>
    );
  }

  if (step === 'confirmBlock') {
    return (
      <View style={styles.group}>
        <Text style={styles.prompt}>
          Block {target.subjectName}? You won't see each other's drops, and
          neither of you can join the other's hangouts. They aren't told.
        </Text>

        <Button
          label={`Block ${target.subjectName}`}
          variant="danger"
          onPress={() => void submitBlock()}
          loading={busy}
        />
        <Button label="Cancel" variant="ghost" onPress={() => setStep('menu')} disabled={busy} />
      </View>
    );
  }

  return (
    <View style={styles.group}>
      {onViewProfile && target.subjectId !== currentUserId ? (
        <Pressable
          accessibilityRole="button"
          onPress={() => {
            onClose();
            onViewProfile(target.subjectId);
          }}
          style={({ pressed }) => [styles.option, pressed ? styles.optionPressed : null]}
        >
          <Text style={styles.optionText}>View {target.subjectName}'s profile</Text>
        </Pressable>
      ) : null}

      <Pressable
        accessibilityRole="button"
        onPress={() => setStep('report')}
        style={({ pressed }) => [styles.option, pressed ? styles.optionPressed : null]}
      >
        <Text style={styles.optionText}>Report this {noun}</Text>
      </Pressable>

      {target.subjectId !== currentUserId ? (
        <Pressable
          accessibilityRole="button"
          onPress={() => setStep('confirmBlock')}
          style={({ pressed }) => [styles.option, pressed ? styles.optionPressed : null]}
        >
          <Text style={[styles.optionText, styles.danger]}>Block {target.subjectName}</Text>
        </Pressable>
      ) : null}

      <Button label="Cancel" variant="ghost" onPress={onClose} />
    </View>
  );
}

const styles = StyleSheet.create({
  group: { gap: spacing.sm },
  prompt: { color: colors.textMuted, fontSize: 14, lineHeight: 21, marginBottom: spacing.xs },
  option: {
    backgroundColor: colors.surfaceRaised,
    borderRadius: radius.md,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.lg - 2,
  },
  optionPressed: { opacity: 0.7 },
  optionText: { color: colors.text, fontSize: 16, fontWeight: '600' },
  danger: { color: colors.danger },
});
