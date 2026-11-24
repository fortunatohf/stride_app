import type { ReactNode } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View, type StyleProp, type ViewStyle } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { colors, radius, type } from '../theme';

export function Screen({ children, edges = ['top'] }: { children: ReactNode; edges?: ('top' | 'bottom')[] }) {
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.bg }} edges={edges}>
      {children}
    </SafeAreaView>
  );
}

export function Card({ children, style, accent }: { children: ReactNode; style?: StyleProp<ViewStyle>; accent?: 'volt' | 'gold' | 'red' }) {
  const border = accent === 'gold' ? 'rgba(255,200,61,0.4)' : accent === 'red' ? 'rgba(255,90,78,0.45)' : accent === 'volt' ? 'rgba(215,255,58,0.4)' : colors.line;
  return <View style={[styles.card, { borderColor: border }, style]}>{children}</View>;
}

export function Button({
  title,
  onPress,
  variant = 'primary',
  loading,
  disabled,
  small,
}: {
  title: string;
  onPress?: () => void;
  variant?: 'primary' | 'secondary' | 'danger';
  loading?: boolean;
  disabled?: boolean;
  small?: boolean;
}) {
  const bg = variant === 'primary' ? colors.volt : variant === 'danger' ? colors.red : colors.surface2;
  const fg = variant === 'secondary' ? colors.text : colors.bg;
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      disabled={disabled || loading}
      style={({ pressed }) => [
        styles.button,
        { backgroundColor: bg, height: small ? 44 : 56, opacity: disabled ? 0.5 : pressed ? 0.85 : 1 },
        variant === 'secondary' && { borderWidth: 1, borderColor: colors.line },
      ]}
    >
      {loading ? <ActivityIndicator color={fg} /> : <Text style={{ color: fg, fontWeight: '700', fontSize: small ? 14.5 : 16.5 }}>{title}</Text>}
    </Pressable>
  );
}

export function Pill({ label, tone = 'default' }: { label: string; tone?: 'default' | 'volt' | 'gold' | 'red' }) {
  const map = {
    default: [colors.surface2, colors.text],
    volt: ['rgba(215,255,58,0.13)', colors.volt],
    gold: ['rgba(255,200,61,0.14)', colors.gold],
    red: ['rgba(255,90,78,0.14)', colors.red],
  } as const;
  const [bg, fg] = map[tone];
  return (
    <View style={[styles.pill, { backgroundColor: bg }]}>
      <Text style={{ color: fg, fontSize: 12, fontWeight: '600' }}>{label}</Text>
    </View>
  );
}

export function Stat({ value, label, align = 'left' }: { value: string; label: string; align?: 'left' | 'center' }) {
  return (
    <View style={{ alignItems: align === 'center' ? 'center' : 'flex-start' }}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={type.kicker}>{label}</Text>
    </View>
  );
}

export function Avatar({ name, size = 36 }: { name: string; size?: number }) {
  const palette = ['#FF9F7A', '#7FD4FF', '#C9B6FF', '#9BE7B0', '#FFD47A', '#FFA3C4'];
  const color = palette[(name.charCodeAt(0) || 0) % palette.length];
  return (
    <View style={{ width: size, height: size, borderRadius: size / 2, backgroundColor: color, alignItems: 'center', justifyContent: 'center' }}>
      <Text style={{ color: colors.bg, fontWeight: '700', fontSize: size * 0.42 }}>{name.slice(0, 1).toUpperCase()}</Text>
    </View>
  );
}

export function SectionTitle({ title, action }: { title: string; action?: ReactNode }) {
  return (
    <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline', marginTop: 22, marginBottom: 10 }}>
      <Text style={type.h2}>{title}</Text>
      {action}
    </View>
  );
}

export function Loading() {
  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', padding: 40 }}>
      <ActivityIndicator color={colors.volt} />
    </View>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor: colors.surface, borderWidth: 1, borderRadius: radius.lg, padding: 16 },
  button: { borderRadius: 18, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 18 },
  pill: { borderRadius: radius.pill, paddingVertical: 5, paddingHorizontal: 11, alignSelf: 'flex-start' },
  statValue: { fontSize: 26, fontWeight: '700', letterSpacing: -0.4, color: colors.text, fontVariant: ['tabular-nums'] },
});
