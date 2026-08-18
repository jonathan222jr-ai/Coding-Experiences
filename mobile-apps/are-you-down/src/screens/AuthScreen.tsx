import { useEffect, useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { sendMagicLink, verifyEmailCode } from '../api/auth';
import type { School } from '../api/schools';
import { Button } from '../components/Button';
import { TextField } from '../components/TextField';
import { useAuth } from '../hooks/useAuth';
import { colors, radius, spacing } from '../theme';

type Step = 'email' | 'sent';

export function AuthScreen() {
  const { linkError, clearLinkError } = useAuth();

  const [step, setStep] = useState<Step>('email');
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [school, setSchool] = useState<School | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // A failed deep link is about this screen, so show it here and hand the
  // provider back a clean slate. Only advance to the code step if we actually
  // know the address — a bad link on a cold start has no email behind it, and
  // "we sent a link to " reads as broken.
  useEffect(() => {
    if (linkError) {
      setError(linkError);
      setStep(email.trim().length > 0 ? 'sent' : 'email');
      clearLinkError();
    }
  }, [linkError, clearLinkError, email]);

  const submitEmail = async () => {
    setBusy(true);
    setError(null);
    try {
      setSchool(await sendMagicLink(email));
      setStep('sent');
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const submitCode = async () => {
    setBusy(true);
    setError(null);
    try {
      // On success the auth listener in AuthProvider swaps this screen out.
      await verifyEmailCode(email, code);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const startOver = () => {
    setStep('email');
    setCode('');
    setError(null);
  };

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView
          contentContainerStyle={styles.content}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.header}>
            <Text style={styles.title}>Are you down?</Text>
            <Text style={styles.tagline}>
              Spontaneous plans with people at your school. Post something, see who's in.
            </Text>
          </View>

          {step === 'email' ? (
            <View style={styles.form}>
              <TextField
                label="School email"
                placeholder="you@school.edu"
                value={email}
                onChangeText={setEmail}
                autoCapitalize="none"
                autoCorrect={false}
                autoComplete="email"
                keyboardType="email-address"
                inputMode="email"
                returnKeyType="go"
                editable={!busy}
                error={error}
                hint="We use it to put you on the right campus. Nothing else."
                onSubmitEditing={() => void submitEmail()}
              />

              <Button
                label="Send me a link"
                onPress={() => void submitEmail()}
                loading={busy}
                disabled={email.trim().length === 0}
              />
            </View>
          ) : (
            <View style={styles.form}>
              <View style={styles.notice}>
                <Text style={styles.noticeTitle}>Check your email</Text>
                <Text style={styles.noticeBody}>
                  We sent a sign-in link to <Text style={styles.strong}>{email}</Text>.
                  {school ? ` You're joining ${school.name}.` : ''}
                </Text>
              </View>

              <TextField
                label="Or enter the six-digit code"
                placeholder="123456"
                value={code}
                onChangeText={setCode}
                keyboardType="number-pad"
                inputMode="numeric"
                autoComplete="one-time-code"
                textContentType="oneTimeCode"
                maxLength={6}
                editable={!busy}
                error={error}
                onSubmitEditing={() => void submitCode()}
              />

              <Button
                label="Sign in"
                onPress={() => void submitCode()}
                loading={busy}
                disabled={code.trim().length < 6}
              />

              <Button
                label="Use a different email"
                variant="ghost"
                onPress={startOver}
                disabled={busy}
              />
            </View>
          )}

          <Text style={styles.footnote}>
            By continuing you agree to be a decent person. Meet in public places.
          </Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  flex: { flex: 1 },
  content: {
    flexGrow: 1,
    padding: spacing.xl,
    justifyContent: 'center',
    gap: spacing.xxl,
  },
  header: { gap: spacing.md },
  title: { color: colors.text, fontSize: 40, fontWeight: '800', letterSpacing: -1 },
  tagline: { color: colors.textMuted, fontSize: 16, lineHeight: 23 },
  form: { gap: spacing.lg },
  notice: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
    gap: spacing.sm,
  },
  noticeTitle: { color: colors.text, fontSize: 16, fontWeight: '700' },
  noticeBody: { color: colors.textMuted, fontSize: 14, lineHeight: 21 },
  strong: { color: colors.text, fontWeight: '600' },
  footnote: {
    color: colors.textMuted,
    fontSize: 12,
    textAlign: 'center',
    lineHeight: 18,
  },
});
