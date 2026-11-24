import { router, useLocalSearchParams } from 'expo-router';
import { useEffect } from 'react';
import { Alert, Text, View } from 'react-native';

import { useRoute } from '../../api/hooks';
import { RouteMap } from '../../components/RouteMap';
import { Button, Card, Pill, Screen, Stat } from '../../components/ui';
import { engineName } from '../../recorder/engine';
import { useRun } from '../../recorder/useRun';
import { colors, formatDuration, formatKm, formatPace, type } from '../../theme';

/** Free run, or a conquest attempt when opened with ?route=<slug>. */
export default function Run() {
  const { route: slug } = useLocalSearchParams<{ route?: string }>();
  const route = useRoute(slug ?? '');
  const run = useRun(route.data);
  const { stats, progress } = run;

  useEffect(() => {
    if (run.phase === 'saved') {
      if (run.activityId) router.replace({ pathname: '/run/[activityId]', params: { activityId: String(run.activityId) } });
      else Alert.alert('Run saved', 'It will upload when you are back online.');
    }
  }, [run.phase, run.activityId]);

  const trail = run.points.map((p) => [p.lat, p.lon] as [number, number]);
  const recordPace = route.data?.champion ? route.data.champion.record_s / (route.data.distance_m / 1000) : null;
  const targetText =
    route.data?.champion && stats.distance > 200
      ? `Hold ${formatPace(recordPace ? recordPace - 1 : null)} to beat ${formatDuration(route.data.champion.record_s)}`
      : null;

  return (
    <Screen>
      <View style={{ height: '46%' }}>
        <RouteMap
          followUser
          zoom={15}
          lines={[
            ...(route.data ? [{ id: 'route', coords: route.data.path, color: colors.volt, width: 5 }] : []),
            ...(trail.length > 1 ? [{ id: 'me', coords: trail, color: '#FFFFFF', width: 5 }] : []),
          ]}
          checkpoints={route.data?.checkpoints}
          start={route.data?.start}
        />
        <View style={{ position: 'absolute', top: 8, left: 12, right: 12, flexDirection: 'row', justifyContent: 'space-between' }}>
          <Pill label={route.data ? `♛ ${route.data.name}` : run.phase === 'recording' ? '● Recording' : 'Free run'} tone={route.data ? 'gold' : 'default'} />
          <Pill label={`GPS ${stats.gps}`} />
        </View>
      </View>

      <View style={{ flex: 1, padding: 20 }}>
        {progress && (
          <Card accent="volt" style={{ marginBottom: 14 }}>
            <Text style={type.h3}>
              {!progress.started
                ? 'Go to the start line to begin'
                : progress.finished
                  ? 'Finish line reached'
                  : `Checkpoint ${progress.passed} of ${progress.total}`}
            </Text>
            {targetText && <Text style={[type.small, { marginTop: 4 }]}>{targetText}</Text>}
          </Card>
        )}

        <Text style={[type.kicker, { textAlign: 'center' }]}>Time</Text>
        <Text style={[type.bigNumber, { textAlign: 'center' }]}>{formatDuration(stats.elapsed)}</Text>
        <View style={{ flexDirection: 'row', justifyContent: 'space-around', marginTop: 16 }}>
          <Stat align="center" value={formatKm(stats.distance)} label="km" />
          <Stat align="center" value={formatDuration(stats.pace)} label="Avg pace" />
          <Stat align="center" value={formatDuration(stats.currentPace)} label="Pace now" />
        </View>

        <View style={{ marginTop: 'auto', gap: 10, paddingBottom: 100 }}>
          {run.error && <Text style={{ color: colors.red, textAlign: 'center' }}>{run.error}</Text>}
          {run.phase === 'idle' || run.phase === 'error' ? (
            <Button title={route.data ? 'Start attempt' : 'Start run'} onPress={run.start} />
          ) : (
            <>
              <Button title="Finish" onPress={run.finish} loading={run.phase === 'saving'} />
              <Button
                title="Discard"
                variant="secondary"
                onPress={() => Alert.alert('Discard this run?', 'It will be deleted from your phone.', [{ text: 'Keep' }, { text: 'Discard', style: 'destructive', onPress: run.discard }])}
              />
            </>
          )}
          <Text style={[type.small, { textAlign: 'center', fontSize: 11 }]}>Recorder: {engineName()} · the server checks every attempt</Text>
        </View>
      </View>
    </Screen>
  );
}
