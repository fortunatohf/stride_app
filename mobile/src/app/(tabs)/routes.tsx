import * as Location from 'expo-location';
import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { FlatList, Pressable, Text, View } from 'react-native';

import { useNearbyRoutes, useRoute } from '../../api/hooks';
import { RouteMap } from '../../components/RouteMap';
import { Card, Pill, Screen, Stat } from '../../components/ui';
import { colors, formatDuration, formatKm, type } from '../../theme';

export default function Routes() {
  const [center, setCenter] = useState<{ lat: number; lon: number }>();
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    Location.getLastKnownPositionAsync().then((p) => p && setCenter({ lat: p.coords.latitude, lon: p.coords.longitude }));
  }, []);

  const routes = useNearbyRoutes(center);
  const detail = useRoute(selected ?? '');
  const sel = routes.data?.find((r) => r.slug === selected);

  return (
    <Screen>
      <View style={{ height: '55%' }}>
        <RouteMap
          center={center ? [center.lat, center.lon] : routes.data?.[0]?.start}
          lines={detail.data ? [{ id: detail.data.slug, coords: detail.data.path }] : []}
          checkpoints={detail.data?.checkpoints ?? []}
          start={detail.data?.start}
        />
      </View>
      {sel && (
        <Pressable onPress={() => router.push({ pathname: '/route/[slug]', params: { slug: sel.slug } })}>
          <Card style={{ margin: 12, marginBottom: 0 }}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
              <Text style={type.h2}>{sel.name}</Text>
              {sel.champion && <Pill tone="gold" label={`♛ ${sel.champion.name}`} />}
            </View>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 12 }}>
              <Stat value={formatKm(sel.distance_m, 1)} label="km" />
              <Stat value={formatDuration(sel.champion?.record_s)} label="Record" />
              <Stat value={String(sel.title_changes)} label="Title changes" />
            </View>
          </Card>
        </Pressable>
      )}
      <FlatList
        data={routes.data ?? []}
        keyExtractor={(r) => r.slug}
        contentContainerStyle={{ padding: 12, paddingBottom: 120 }}
        renderItem={({ item }) => (
          <Pressable onPress={() => setSelected(item.slug)}>
            <View style={{ paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: colors.line, flexDirection: 'row', justifyContent: 'space-between' }}>
              <View>
                <Text style={[type.h3, selected === item.slug && { color: colors.volt }]}>{item.name}</Text>
                <Text style={type.small}>{formatKm(item.distance_m, 1)} km</Text>
              </View>
              <Text style={{ color: colors.text, fontVariant: ['tabular-nums'] }}>{formatDuration(item.champion?.record_s)}</Text>
            </View>
          </Pressable>
        )}
      />
    </Screen>
  );
}
