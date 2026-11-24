import Mapbox, { Camera, CircleLayer, LineLayer, MapView, ShapeSource, UserLocation } from '@rnmapbox/maps';
import { StyleSheet, Text, View, type StyleProp, type ViewStyle } from 'react-native';

import type { LatLon } from '../api/types';
import { colors } from '../theme';

const TOKEN = process.env.EXPO_PUBLIC_MAPBOX_TOKEN;
if (TOKEN) Mapbox.setAccessToken(TOKEN);

type Line = { id: string; coords: LatLon[]; color?: string; width?: number };

/** Dark map with route lines, checkpoints and the runner. Coordinates are [lat, lon] (Mapbox wants [lon, lat]). */
export function RouteMap({
  lines = [],
  checkpoints = [],
  start,
  center,
  zoom = 13.5,
  followUser = false,
  style,
  onPressLine,
}: {
  lines?: Line[];
  checkpoints?: LatLon[];
  start?: LatLon;
  center?: LatLon;
  zoom?: number;
  followUser?: boolean;
  style?: StyleProp<ViewStyle>;
  onPressLine?: (id: string) => void;
}) {
  if (!TOKEN) {
    return (
      <View style={[styles.placeholder, style]}>
        <Text style={{ color: colors.muted, textAlign: 'center' }}>Set EXPO_PUBLIC_MAPBOX_TOKEN to show the map</Text>
      </View>
    );
  }
  const first = center ?? lines[0]?.coords[0] ?? start;
  return (
    <MapView style={[{ flex: 1 }, style]} styleURL={Mapbox.StyleURL.Dark} logoEnabled={false} scaleBarEnabled={false} attributionPosition={{ bottom: 8, left: 8 }}>
      <Camera
        followUserLocation={followUser}
        centerCoordinate={!followUser && first ? [first[1], first[0]] : undefined}
        zoomLevel={zoom}
        animationDuration={0}
      />
      <UserLocation visible />
      {lines.map((l) => (
        <ShapeSource
          key={l.id}
          id={`src-${l.id}`}
          shape={{ type: 'Feature', properties: { id: l.id }, geometry: { type: 'LineString', coordinates: l.coords.map(([lat, lon]) => [lon, lat]) } }}
          onPress={() => onPressLine?.(l.id)}
          hitbox={{ width: 24, height: 24 }}
        >
          <LineLayer id={`glow-${l.id}`} style={{ lineColor: l.color ?? colors.volt, lineWidth: (l.width ?? 5) * 3, lineOpacity: 0.18, lineCap: 'round', lineJoin: 'round' }} />
          <LineLayer id={`line-${l.id}`} style={{ lineColor: l.color ?? colors.volt, lineWidth: l.width ?? 5, lineCap: 'round', lineJoin: 'round' }} />
        </ShapeSource>
      ))}
      {checkpoints.length > 0 && (
        <ShapeSource
          id="checkpoints"
          shape={{ type: 'FeatureCollection', features: checkpoints.map(([lat, lon], i) => ({ type: 'Feature', properties: { i }, geometry: { type: 'Point', coordinates: [lon, lat] } })) }}
        >
          <CircleLayer id="cp" style={{ circleRadius: 6, circleColor: colors.bg, circleStrokeColor: colors.volt, circleStrokeWidth: 2.5 }} />
        </ShapeSource>
      )}
      {start && (
        <ShapeSource id="start" shape={{ type: 'Feature', properties: {}, geometry: { type: 'Point', coordinates: [start[1], start[0]] } }}>
          <CircleLayer id="start-dot" style={{ circleRadius: 9, circleColor: colors.volt, circleStrokeColor: colors.bg, circleStrokeWidth: 3 }} />
        </ShapeSource>
      )}
    </MapView>
  );
}

const styles = StyleSheet.create({
  placeholder: { backgroundColor: '#111419', alignItems: 'center', justifyContent: 'center', padding: 24 },
});
