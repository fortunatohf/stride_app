import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { ScrollView, Text, TextInput, View } from 'react-native';

import { ApiError } from '../../api/client';
import { useActivity, usePublishRoute } from '../../api/hooks';
import { RouteMap } from '../../components/RouteMap';
import { Button, Card, Loading, Pill, Screen, Stat } from '../../components/ui';
import { colors, formatDuration, formatKm, formatPace, type } from '../../theme';

const REASONS: Record<string, string> = {
  no_start: "You didn't pass the start line",
  no_finish: "You didn't reach the finish line",
  distance_short: 'Shorter than the route — looks like a shortcut',
  distance_long: 'Much longer than the route',
  off_route: 'Part of the run left the route',
  too_fast: 'Speed looks like a bike or a car',
  gps_gap: 'GPS signal dropped for over a minute',
  gps_unreliable: 'GPS signal was too unreliable',
  manual_activity: 'Manually entered activities do not count',
};
const PROBLEMS: Record<string, string> = {
  too_short: 'Routes must be at least 3 km',
  too_long: 'Routes can be at most 10 km',
  duplicate_route: 'A very similar route already exists',
  poor_gps: 'GPS quality was too low on this run',
  'near_privacy_zone:start': 'The start is too close to one of your privacy zones',
  'near_privacy_zone:finish': 'The finish is too close to one of your privacy zones',
};
const reason = (r: string) => (r.startsWith('missed_checkpoint') ? `Missed checkpoint ${r.split(':')[1]} (or ran the wrong direction)` : (REASONS[r] ?? r));

/** Result screen after a run: attempts on routes (title won?), or publish the run as a new route. */
export default function RunResult() {
  const { activityId } = useLocalSearchParams<{ activityId: string }>();
  const activity = useActivity(Number(activityId));
  const publish = usePublishRoute();
  const [name, setName] = useState('');
  const [problems, setProblems] = useState<string[]>([]);

  const a = activity.data;
  if (!a) return <Loading />;
  const checking = a.state === 'received';
  const won = a.attempts.find((x) => x.took_title);

  const submit = () =>
    publish.mutate(
      { activity_id: a.id, name: name.trim() },
      {
        onSuccess: () => setProblems([]),
        onError: (e) => setProblems(e instanceof ApiError ? ((e.body as { problems?: string[] })?.problems ?? [e.message]) : ['Something went wrong']),
      },
    );

  return (
    <Screen>
      <ScrollView contentContainerStyle={{ padding: 20, paddingBottom: 60 }}>
        <Text style={type.kicker}>{won ? 'Title won' : 'Run complete'}</Text>
        <Text style={[type.h1, { marginTop: 6 }]}>{won ? `${won.route_name} is yours` : 'Nice run'}</Text>

        <View style={{ height: 190, borderRadius: 20, overflow: 'hidden', marginTop: 16, borderWidth: 1, borderColor: colors.line }}>
          <RouteMap lines={[{ id: 'run', coords: a.path, color: '#FFFFFF' }]} zoom={13} />
        </View>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 16 }}>
          <Stat value={formatKm(a.distance_m)} label="km" />
          <Stat value={formatDuration(a.duration_s)} label="Time" />
          <Stat value={formatDuration(a.duration_s / (a.distance_m / 1000))} label="Pace /km" />
        </View>

        {checking && <Text style={[type.small, { marginTop: 18 }]}>Checking your run against nearby routes…</Text>}
        {a.attempts.map((x) => (
          <Card key={x.id} accent={x.took_title ? 'gold' : x.valid ? 'volt' : 'red'} style={{ marginTop: 14 }}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
              <Text style={type.h3}>{x.route_name}</Text>
              <Pill tone={x.took_title ? 'gold' : x.valid ? 'volt' : 'red'} label={x.took_title ? '♛ Champion' : x.valid ? (x.eligible ? 'Valid' : 'Valid · not posted') : 'Not counted'} />
            </View>
            {x.valid ? (
              <Text style={[type.small, { marginTop: 6 }]}>
                {formatDuration(x.elapsed_s)} · {formatPace(x.elapsed_s && x.distance_m ? x.elapsed_s / (x.distance_m / 1000) : null)}
                {x.personal_best ? ' · personal best' : ''}
              </Text>
            ) : (
              x.reasons.map((r) => (
                <Text key={r} style={[type.small, { marginTop: 4 }]}>
                  {reason(r)}
                </Text>
              ))
            )}
            {!x.eligible && x.valid && <Text style={[type.small, { marginTop: 4 }]}>Turn on "Post watch runs" in Devices to count watch runs.</Text>}
          </Card>
        ))}

        {!checking && !won && (
          <Card style={{ marginTop: 20 }}>
            <Text style={type.h2}>Publish as a route?</Text>
            <Text style={[type.small, { marginTop: 4 }]}>Others can try to beat your time. You become founder and first champion after a quick review.</Text>
            {publish.isSuccess ? (
              <Text style={{ color: colors.volt, marginTop: 12 }}>Submitted for review. You'll get a notification when it is live.</Text>
            ) : (
              <>
                <TextInput
                  value={name}
                  onChangeText={setName}
                  placeholder="Route name, e.g. Zilker Loop"
                  placeholderTextColor={colors.muted2}
                  style={{ marginTop: 12, height: 50, borderRadius: 14, borderWidth: 1, borderColor: colors.line, paddingHorizontal: 14, color: colors.text }}
                />
                {problems.map((p) => (
                  <Text key={p} style={{ color: colors.red, marginTop: 6 }}>
                    {PROBLEMS[p] ?? p}
                  </Text>
                ))}
                <View style={{ marginTop: 12 }}>
                  <Button title="Publish route" onPress={submit} loading={publish.isPending} disabled={name.trim().length < 3} />
                </View>
              </>
            )}
          </Card>
        )}

        <View style={{ marginTop: 20 }}>
          <Button variant="secondary" title="Done" onPress={() => router.replace('/')} />
        </View>
      </ScrollView>
    </Screen>
  );
}
