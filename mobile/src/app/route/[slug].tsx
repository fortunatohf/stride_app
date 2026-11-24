import { router, useLocalSearchParams } from 'expo-router';
import { Pressable, ScrollView, Text, View } from 'react-native';

import { useCreateComeback, useLeaderboard, useMe, useRoute } from '../../api/hooks';
import { RouteMap } from '../../components/RouteMap';
import { Avatar, Button, Card, Loading, Pill, Screen, SectionTitle } from '../../components/ui';
import { colors, formatDuration, formatKm, formatPace, type } from '../../theme';

export default function RouteCard() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const route = useRoute(slug);
  const board = useLeaderboard(slug);
  const me = useMe();
  const comeback = useCreateComeback();

  if (!route.data) return <Loading />;
  const r = route.data;
  const champ = r.champion;
  const iAmChampion = champ && me.data && champ.user_id === me.data.id;
  const myRow = board.data?.rows.find((x) => x.me);

  return (
    <Screen>
      <ScrollView contentContainerStyle={{ paddingBottom: 140 }}>
        <View style={{ height: 260 }}>
          <RouteMap lines={[{ id: r.slug, coords: r.path }]} checkpoints={r.checkpoints} start={r.start} zoom={13.2} />
          <Pressable onPress={() => router.back()} style={{ position: 'absolute', top: 10, left: 14, backgroundColor: 'rgba(11,12,15,0.8)', borderRadius: 20, padding: 10 }}>
            <Text style={{ color: colors.text, fontSize: 16 }}>‹</Text>
          </Pressable>
        </View>
        <View style={{ padding: 20 }}>
          <Text style={type.h1}>{r.name}</Text>
          <Text style={[type.small, { marginTop: 6 }]}>
            {formatKm(r.distance_m, 1)} km {r.is_loop ? 'loop' : 'point to point'} · {r.checkpoints.length} checkpoints
          </Text>

          {champ && (
            <Card accent="gold" style={{ marginTop: 16, flexDirection: 'row', alignItems: 'center', gap: 12 }}>
              <Avatar name={champ.name} size={46} />
              <View style={{ flex: 1 }}>
                <Text style={[type.kicker, { color: colors.gold }]}>Champion</Text>
                <Text style={[type.h3, { fontSize: 16 }]}>{champ.name}</Text>
              </View>
              <View style={{ alignItems: 'flex-end' }}>
                <Text style={[type.h2, { fontVariant: ['tabular-nums'] }]}>{formatDuration(champ.record_s)}</Text>
                <Text style={type.small}>{formatPace(champ.record_s / (r.distance_m / 1000))}</Text>
              </View>
            </Card>
          )}
          <View style={{ flexDirection: 'row', gap: 8, marginTop: 10 }}>
            {r.founder && <Pill label={`Founded by ${r.founder}`} />}
            <Pill label={`${r.title_changes} title changes`} />
          </View>

          <SectionTitle title="Leaderboard" />
          {(board.data?.rows ?? []).map((row) => (
            <View key={row.user_id} style={{ flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: colors.line }}>
              <Text style={{ width: 22, color: colors.muted, fontWeight: '700' }}>{row.rank}</Text>
              <Avatar name={row.name} size={30} />
              <Text style={[type.body, { flex: 1 }]}>
                {row.name}
                {row.me ? <Text style={{ color: colors.muted }}> (you)</Text> : null}
              </Text>
              <Text style={{ color: colors.text, fontWeight: '600', fontVariant: ['tabular-nums'] }}>{formatDuration(row.elapsed_s)}</Text>
            </View>
          ))}

          {r.history.length > 0 && (
            <>
              <SectionTitle title="Title history" />
              {r.history.slice(0, 5).map((h, i) => (
                <Text key={i} style={[type.small, { marginBottom: 6 }]}>
                  {h.new_holder} {h.previous_holder ? `took it from ${h.previous_holder}` : 'founded it'} · {formatDuration(h.new_record_s)}
                </Text>
              ))}
            </>
          )}
        </View>
      </ScrollView>

      <View style={{ position: 'absolute', left: 20, right: 20, bottom: 30, gap: 10 }}>
        <Button title={iAmChampion ? 'Defend your record' : 'Try to conquer'} onPress={() => router.push({ pathname: '/run', params: { route: r.slug } })} />
        {!iAmChampion && myRow && (
          <Button
            variant="secondary"
            title="Plan my comeback"
            loading={comeback.isPending}
            onPress={() => comeback.mutate(r.slug, { onSuccess: () => router.push('/train') })}
          />
        )}
      </View>
    </Screen>
  );
}
