import { useState } from 'react';
import { KeyboardAvoidingView, Platform, StyleSheet, Text, TextInput, View } from 'react-native';

import { login } from '../api/client';
import { Button, Screen } from '../components/ui';
import { colors, type } from '../theme';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      await login(username.trim(), password); // the root layout redirects once signed in
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Sign in failed');
    } finally {
      setBusy(false);
    }
  };

  return (
    <Screen>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.wrap}>
        <Text style={styles.wordmark}>STRYDE</Text>
        <Text style={[type.h1, { marginTop: 24 }]}>Run it. Own it.{'\n'}Defend it.</Text>
        <Text style={[type.small, { marginTop: 10 }]}>Sign in to chase routes in your city.</Text>
        <View style={{ gap: 12, marginTop: 32 }}>
          <TextInput style={styles.input} placeholder="Username" placeholderTextColor={colors.muted2} autoCapitalize="none" value={username} onChangeText={setUsername} />
          <TextInput style={styles.input} placeholder="Password" placeholderTextColor={colors.muted2} secureTextEntry value={password} onChangeText={setPassword} />
          {error && <Text style={{ color: colors.red }}>{error}</Text>}
          <Button title="Sign in" onPress={submit} loading={busy} disabled={!username || !password} />
        </View>
      </KeyboardAvoidingView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  wrap: { flex: 1, padding: 24, justifyContent: 'center' },
  wordmark: { color: colors.text, fontSize: 28, fontWeight: '900', fontStyle: 'italic', letterSpacing: -0.5 },
  input: { height: 54, borderRadius: 14, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.line, paddingHorizontal: 16, color: colors.text, fontSize: 16 },
});
