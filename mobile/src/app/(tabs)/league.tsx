import { ScrollView, Text, View } from 'react-native';

import { useLeague } from '../../api/hooks';
import { Avatar, Card, Loading, Screen } from '../../components/ui';
import { colors, type } from '../../theme';

const TIERS = ['bronze', 'silver', 'gold', 'elite'];
const LABEL: Record<string, string> = { conquer: 'Conquer a route', pb: 'Personal best', challenge: 'Official challenge' };

export default function League() {
  const { data, isLoading } = useLeague();
  if (isLoading) return <Loading />;
  if (!data?.season) {
    return (
      <Screen>
        <View style={{ padding: 20 }}>
          <Text style={type.h1}>League</Text>
          <Text style={[type.small, { marginTop: 8 }]}>No season is running in your city yet.</Text>
        </View>
      </Screen>
    );
  }
  const rows = data.standings ?? [];
  const daysLeft = Math.max(0, Math.ceil((new Date(data.season.ends_on).getTime() - Date.now()) / 86_400_000));

  return (
    <Screen>
      <ScrollView contentContainerStyle={{ padding: 20, paddingBottom: 120 }}>
        <Text style={type.kicker}>
          Season {data.season.number} · {data.season.city}
        </Text>
        <Text style={[type.h1, { marginTop: 6, textTransform: 'capitalize' }]}>{data.tier} League</Text>
        <View style={{ flexDirection: 'row', gap: 6, marginTop: 14 }}>
          {TIERS.map((t) => (
            <View key={t} style={{ flex: 1, paddingVertical: 8, borderRadius: 12, alignItems: 'center', backgroundColor: t === data.tier ? '#C9CED6' : colors.surface2 }}>
              <Text style={{ fontSize: 12, fontWeight: '700', color: t === data.tier ? colors.bg : colors.muted, textTransform: 'capitalize' }}>{t}</Text>
            </View>
          ))}
        </View>
        <Text style={[type.small, { marginTop: 12 }]}>Ends in {daysLeft} days · top 3 move up, bottom 3 move down</Text>

        <View style={{ marginTop: 12 }}>
          {rows.map((r) => (
            <View key={r.user_id}>
              <View
                style={{
                  flexDirection: 'row',
                  alignItems: 'center',
                  gap: 12,
                  paddingVertical: 11,
                  paddingHorizontal: r.me ? 10 : 0,
                  borderRadius: 14,
                  backgroundColor: r.me ? 'rgba(215,255,58,0.09)' : 'transparent',
                }}
              >
                <Text style={{ width: 22, fontWeight: '700', color: r.rank <= 3 ? colors.volt : colors.muted }}>{r.rank}</Text>
                <Avatar name={r.name} size={32} />
                <Text style={[type.body, { flex: 1 }]}>
                  {r.name}
                  {r.me ? <Text style={{ color: colors.muted }}> (you)</Text> : null}
                </Text>
                <Text style={{ color: colors.text, fontWeight: '700', fontVariant: ['tabular-nums'] }}>{r.points} pts</Text>
              </View>
              {r.rank === 3 && rows.length > 3 && (
                <Text style={{ color: colors.volt, fontSize: 11.5, fontWeight: '700', textAlign: 'center', marginVertical: 6 }}>— PROMOTION ZONE —</Text>
              )}
            </View>
          ))}
        </View>

        <Card style={{ marginTop: 16 }}>
          <Text style={type.h3}>How you earn points</Text>
          {Object.entries(data.points_table ?? {}).map(([k, v]) => (
            <View key={k} style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 8 }}>
              <Text style={type.small}>{LABEL[k] ?? k}</Text>
              <Text style={{ color: colors.text }}>{v}</Text>
            </View>
          ))}
          <Text style={[type.small, { marginTop: 8 }]}>Weekly cap: {data.weekly_cap} pts. Premium never adds points.</Text>
        </Card>
      </ScrollView>
    </Screen>
  );
}
