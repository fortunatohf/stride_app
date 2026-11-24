import { Link, router } from 'expo-router';
import { Pressable, ScrollView, Text, View } from 'react-native';

import { useAlerts, useLeague, useMe, useNearbyRoutes, usePlan } from '../../api/hooks';
import { Avatar, Button, Card, Pill, Screen, SectionTitle } from '../../components/ui';
import { colors, formatDuration, formatKm, type } from '../../theme';

export default function Home() {
  const me = useMe();
  const alerts = useAlerts();
  const league = useLeague();
  const plan = usePlan();
  const routes = useNearbyRoutes();

  const name = me.data?.display_name || me.data?.username || '';
  const lost = alerts.data?.[0];
  const today = new Date().toLocaleDateString('en-CA'); // local YYYY-MM-DD
  const session = plan.data?.sessions.find((s) => s.date === today);
  const mine = league.data?.standings?.find((s) => s.me);

  return (
    <Screen>
      <ScrollView contentContainerStyle={{ padding: 20, paddingBottom: 120 }}>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Text style={{ color: colors.text, fontSize: 22, fontWeight: '900', fontStyle: 'italic' }}>STRYDE</Text>
          <Pressable onPress={() => router.push('/devices')}>
            <Avatar name={name || '?'} size={34} />
          </Pressable>
        </View>

        <Text style={[type.h1, { marginTop: 20 }]}>
          Hi, {name}.{'\n'}
          <Text style={{ color: colors.muted, fontWeight: '600' }}>{lost ? 'Your title is under attack.' : 'Pick a route to chase.'}</Text>
        </Text>

        {lost && (
          <Card accent="red" style={{ marginTop: 18 }}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
              <Pill label="Title lost" tone="red" />
              <Text style={type.small}>
                {lost.route_name} · {formatKm(lost.distance_m, 1)} km
              </Text>
            </View>
            <View style={{ flexDirection: 'row', gap: 12, alignItems: 'center', marginTop: 14 }}>
              <Avatar name={lost.by} size={40} />
              <View style={{ flex: 1 }}>
                <Text style={type.h3}>{lost.by} took your route</Text>
                <Text style={type.small}>
                  {formatDuration(lost.their_time_s)} vs your {formatDuration(lost.your_time_s)}
                </Text>
              </View>
            </View>
            <View style={{ flexDirection: 'row', gap: 10, marginTop: 14 }}>
              <View style={{ flex: 1 }}>
                <Button small title="Win it back" onPress={() => router.push({ pathname: '/run', params: { route: lost.route } })} />
              </View>
              <View style={{ flex: 1 }}>
                <Button small variant="secondary" title="See rivalry" onPress={() => router.push({ pathname: '/route/[slug]', params: { slug: lost.route } })} />
              </View>
            </View>
          </Card>
        )}

        <View style={{ flexDirection: 'row', gap: 10, marginTop: 12 }}>
          <Card style={{ flex: 1 }}>
            <Text style={type.kicker}>Today</Text>
            <Text style={[type.h3, { marginTop: 8 }]}>{session ? session.title : 'No session planned'}</Text>
            <Text style={[type.small, { marginTop: 3 }]}>{session?.detail ?? 'Start a comeback plan from any route'}</Text>
          </Card>
          <Card style={{ flex: 1 }}>
            <Text style={type.kicker}>League</Text>
            <Text style={[type.h2, { marginTop: 6 }]}>{mine ? `#${mine.rank}` : '—'}</Text>
            <Text style={type.small}>{league.data?.tier ? `${league.data.tier} · ${league.data.season?.city}` : 'No active season'}</Text>
          </Card>
        </View>

        <SectionTitle
          title="Routes near you"
          action={
            <Link href="/routes" style={{ color: colors.volt }}>
              See map
            </Link>
          }
        />
        {(routes.data ?? []).slice(0, 5).map((r) => (
          <Pressable key={r.slug} onPress={() => router.push({ pathname: '/route/[slug]', params: { slug: r.slug } })}>
            <Card style={{ marginBottom: 10, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
              <View>
                <Text style={type.h3}>{r.name}</Text>
                <Text style={type.small}>
                  {formatKm(r.distance_m, 1)} km · {r.title_changes} title changes
                </Text>
              </View>
              {r.champion && <Pill tone="gold" label={`♛ ${formatDuration(r.champion.record_s)}`} />}
            </Card>
          </Pressable>
        ))}
        {routes.data?.length === 0 && <Text style={type.small}>No routes nearby yet. Run one and publish it to become its first champion.</Text>}
      </ScrollView>
    </Screen>
  );
}
